from __future__ import annotations


from aiogram import Bot
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import (
    Achievement,
    UserAchievement,
    InviteToken,
    VipSubscription,
    Badge,
    UserBadge,
    UserStats,
    UserMissionEntry,
)

PREDEFINED_ACHIEVEMENTS = [
    {
        "id": "first_message",
        "name": "Primer Mensaje",
        "condition_type": "messages",
        "condition_value": 1,
        "reward_text": "🏅 ¡Logro desbloqueado: Primer Mensaje! Has enviado 1 mensaje.",
    },
    {
        "id": "conversador",
        "name": "Conversador",
        "condition_type": "messages",
        "condition_value": 100,
        "reward_text": "🏅 ¡Logro desbloqueado: Conversador! Has enviado 100 mensajes.",
    },
    {
        "id": "invitador",
        "name": "Invitador",
        "condition_type": "invites",
        "condition_value": 5,
        "reward_text": "🏅 ¡Logro desbloqueado: Invitador! Has invitado a 5 amigos.",
    },
    {
        "id": "checkin_7dias",
        "name": "Check-in 7 d\u00edas",
        "condition_type": "checkins",
        "condition_value": 7,
        "reward_text": "🏅 ¡Logro desbloqueado: Check-in 7 días!",
    },
    {
        "id": "vip_supporter",
        "name": "VIP Supporter",
        "condition_type": "vip",
        "condition_value": 1,
        "reward_text": "🏅 ¡Logro desbloqueado: VIP Supporter! Gracias por tu suscripción.",
    },
]

# Convenience mapping by ID for easy lookups (used in profile views)
ACHIEVEMENTS = {a["id"]: a for a in PREDEFINED_ACHIEVEMENTS}
# Backwards compatibility alias in case external code imports singular name
ACHIEVEMENT = ACHIEVEMENTS


class AchievementService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def ensure_achievements_exist(self) -> None:
        stmt = select(Achievement)
        existing = {a.id for a in (await self.session.execute(stmt)).scalars().all()}
        for ach in PREDEFINED_ACHIEVEMENTS:
            if ach["id"] not in existing:
                obj = Achievement(**ach)
                self.session.add(obj)
        if self.session.new:
            await self.session.commit()

    async def _grant(self, user_id: int, achievement: Achievement, *, bot: Bot | None = None) -> bool:
        stmt = select(UserAchievement).where(
            UserAchievement.user_id == user_id,
            UserAchievement.achievement_id == achievement.id,
        )
        result = await self.session.execute(stmt)
        if result.scalar_one_or_none():
            return False
        obj = UserAchievement(user_id=user_id, achievement_id=achievement.id)
        self.session.add(obj)
        await self.session.commit()
        if bot:
            await bot.send_message(user_id, achievement.reward_text)
        return True

    async def _check_and_grant(self, user_id: int, condition_type: str, value: int, bot: Bot | None = None):
        await self.ensure_achievements_exist()
        stmt = select(Achievement).where(
            Achievement.condition_type == condition_type,
            Achievement.condition_value <= value,
        )
        achievements = (await self.session.execute(stmt)).scalars().all()
        for ach in achievements:
            await self._grant(user_id, ach, bot=bot)

    async def check_message_achievements(self, user_id: int, messages_sent: int, *, bot: Bot | None = None):
        await self._check_and_grant(user_id, "messages", messages_sent, bot=bot)

    async def check_checkin_achievements(self, user_id: int, streak: int, *, bot: Bot | None = None):
        await self._check_and_grant(user_id, "checkins", streak, bot=bot)

    async def check_invite_achievements(self, user_id: int, *, bot: Bot | None = None):
        stmt = select(func.count()).select_from(InviteToken).where(
            InviteToken.created_by == user_id,
            InviteToken.used_by.is_not(None),
        )
        count = (await self.session.execute(stmt)).scalar() or 0
        await self._check_and_grant(user_id, "invites", count, bot=bot)

    async def check_vip_achievement(self, user_id: int, *, bot: Bot | None = None):
        stmt = select(func.count()).select_from(VipSubscription).where(VipSubscription.user_id == user_id)
        count = (await self.session.execute(stmt)).scalar() or 0
        await self._check_and_grant(user_id, "vip", count, bot=bot)

    # ----- Badge related methods -----
    async def _badge_condition_met(self, user_id: int, badge: Badge) -> bool:
        progress = await self.session.get(UserStats, user_id)
        if not progress:
            return False
        if badge.condition_type == "messages":
            return progress.messages_sent >= badge.condition_value
        if badge.condition_type == "login_streak":
            return progress.checkin_streak >= badge.condition_value
        if badge.condition_type == "missions":
            stmt = select(func.count()).select_from(UserMissionEntry).where(
                UserMissionEntry.user_id == user_id,
                UserMissionEntry.completed == True,
            )
            count = (await self.session.execute(stmt)).scalar() or 0
            return count >= badge.condition_value
        if badge.condition_type == "invites":
            stmt = select(func.count()).select_from(InviteToken).where(
                InviteToken.created_by == user_id,
                InviteToken.used_by.is_not(None),
            )
            count = (await self.session.execute(stmt)).scalar() or 0
            return count >= badge.condition_value
        return False

    async def check_user_badges(self, user_id: int) -> list[Badge]:
        stmt = select(Badge).where(Badge.is_active == True)
        badges = (await self.session.execute(stmt)).scalars().all()
        unlockable = []
        for badge in badges:
            stmt = select(UserBadge).where(
                UserBadge.user_id == user_id,
                UserBadge.badge_id == badge.id,
            )
            existing = (await self.session.execute(stmt)).scalar_one_or_none()
            if existing:
                continue
            if await self._badge_condition_met(user_id, badge):
                unlockable.append(badge)
        return unlockable

    async def award_badge(self, user_id: int, badge_id: int, *, force: bool = False) -> bool:
        badge = await self.session.get(Badge, badge_id)
        if not badge or not badge.is_active:
            return False
        stmt = select(UserBadge).where(
            UserBadge.user_id == user_id,
            UserBadge.badge_id == badge_id,
        )
        existing = (await self.session.execute(stmt)).scalar_one_or_none()
        if existing:
            return False
        if not force and not await self._badge_condition_met(user_id, badge):
            return False
        self.session.add(UserBadge(user_id=user_id, badge_id=badge_id))
        await self.session.commit()
        return True

    async def get_user_badges(self, user_id: int) -> list[Badge]:
        stmt = (
            select(Badge)
            .join(UserBadge, UserBadge.badge_id == Badge.id)
            .where(UserBadge.user_id == user_id)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()
