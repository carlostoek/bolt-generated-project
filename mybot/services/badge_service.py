from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from aiogram import Bot

from database.models import Badge, UserBadge, User, UserStats
import re

class BadgeService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_badge(self, name: str, description: str, requirement: str, emoji: str | None = None) -> Badge:
        badge = Badge(name=name.strip(), description=description.strip(), requirement=requirement.strip(), emoji=emoji)
        self.session.add(badge)
        await self.session.commit()
        await self.session.refresh(badge)
        return badge

    async def list_badges(self) -> list[Badge]:
        result = await self.session.execute(select(Badge).order_by(Badge.id))
        return result.scalars().all()

    async def delete_badge(self, badge_id: int) -> bool:
        badge = await self.session.get(Badge, badge_id)
        if not badge:
            return False
        await self.session.delete(badge)
        await self.session.commit()
        return True

    async def grant_badge(self, user_id: int, badge: Badge) -> bool:
        stmt = select(UserBadge).where(
            UserBadge.user_id == user_id,
            UserBadge.badge_id == badge.id,
        )
        existing = (await self.session.execute(stmt)).scalar_one_or_none()
        if existing:
            return False
        self.session.add(UserBadge(user_id=user_id, badge_id=badge.id))
        await self.session.commit()
        return True

    async def check_badges(self, user: User, progress: UserStats, bot: Bot | None = None):
        badges = await self.list_badges()
        for badge in badges:
            stmt = select(UserBadge).where(
                UserBadge.user_id == user.id,
                UserBadge.badge_id == badge.id,
            )
            existing = (await self.session.execute(stmt)).scalar_one_or_none()
            if existing:
                continue
            req = badge.requirement.lower()
            granted = False
            lvl_match = re.search(r"nivel\s*(\d+)", req)
            msg_match = re.search(r"(\d+)\s*mensajes", req)
            if lvl_match and user.level >= int(lvl_match.group(1)):
                granted = True
            if msg_match and progress.messages_sent >= int(msg_match.group(1)):
                granted = True
            if granted:
                await self.grant_badge(user.id, badge)
                if bot:
                    text = f"🏅 Has obtenido la insignia {badge.emoji or ''} {badge.name}!"
                    await bot.send_message(user.id, text)
