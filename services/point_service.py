from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from database.models import User, UserStats
from utils.user_roles import get_points_multiplier
from aiogram import Bot
from services.level_service import LevelService
from services.achievement_service import AchievementService
from services.event_service import EventService
import datetime
import logging

logger = logging.getLogger(__name__)

class PointService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def _get_or_create_progress(self, user_id: int) -> UserStats:
        progress = await self.session.get(UserStats, user_id)
        if not progress:
            progress = UserStats(user_id=user_id)
            self.session.add(progress)
            await self.session.commit()
            await self.session.refresh(progress)
        return progress

    async def award_message(self, user_id: int, bot: Bot) -> UserStats | None:
        progress = await self._get_or_create_progress(user_id)
        now = datetime.datetime.utcnow()
        if progress.last_activity_at and (now - progress.last_activity_at).total_seconds() < 30:
            return None
        progress = await self.add_points(user_id, 1, bot=bot)
        progress.messages_sent += 1
        await self.session.commit()
        ach_service = AchievementService(self.session)
        await ach_service.check_message_achievements(user_id, progress.messages_sent, bot=bot)
        new_badges = await ach_service.check_user_badges(user_id)
        for badge in new_badges:
            await ach_service.award_badge(user_id, badge.id)
            if bot:
                await bot.send_message(
                    user_id,
                    f"🏅 Has obtenido la insignia {badge.icon or ''} {badge.name}!",
                )
        return progress

    async def award_reaction(
        self, user: User, message_id: int, bot: Bot
    ) -> UserStats | None:
        progress = await self.add_points(user.id, 0.5, bot=bot)
        ach_service = AchievementService(self.session)
        new_badges = await ach_service.check_user_badges(user.id)
        for badge in new_badges:
            await ach_service.award_badge(user.id, badge.id)
            if bot:
                await bot.send_message(
                    user.id,
                    f"🏅 Has obtenido la insignia {badge.icon or ''} {badge.name}!",
                )
        return progress

    async def award_poll(self, user_id: int, bot: Bot) -> UserStats:
        progress = await self.add_points(user_id, 2, bot=bot)
        ach_service = AchievementService(self.session)
        new_badges = await ach_service.check_user_badges(user_id)
        for badge in new_badges:
            await ach_service.award_badge(user_id, badge.id)
            if bot:
                await bot.send_message(
                    user_id,
                    f"🏅 Has obtenido la insignia {badge.icon or ''} {badge.name}!",
                )
        return progress

    async def daily_checkin(self, user_id: int, bot: Bot) -> tuple[bool, UserStats]:
        progress = await self._get_or_create_progress(user_id)
        now = datetime.datetime.utcnow()
        if progress.last_checkin_at and (now - progress.last_checkin_at).total_seconds() < 86400:
            return False, progress
        progress = await self.add_points(user_id, 10, bot=bot)
        if progress.last_checkin_at and (now.date() - progress.last_checkin_at.date()).days == 1:
            progress.checkin_streak += 1
        else:
            progress.checkin_streak = 1
        progress.last_checkin_at = now
        await self.session.commit()
        ach_service = AchievementService(self.session)
        await ach_service.check_checkin_achievements(user_id, progress.checkin_streak, bot=bot)
        new_badges = await ach_service.check_user_badges(user_id)
        for badge in new_badges:
            await ach_service.award_badge(user_id, badge.id)
            if bot:
                await bot.send_message(
                    user_id,
                    f"🏅 Has obtenido la insignia {badge.icon or ''} {badge.name}!",
                )
        return True, progress

    async def add_points(self, user_id: int, points: float, *, bot: Bot | None = None) -> UserStats:
        user = await self.session.get(User, user_id)
        if not user:
            logger.warning(
                f"Attempted to add points to non-existent user {user_id}. Creating new user."
            )
            user = User(id=user_id, points=0)
            self.session.add(user)
            await self.session.commit()
            await self.session.refresh(user)

        multiplier = 1
        if bot:
            multiplier = await get_points_multiplier(bot, user_id, session=self.session)
            event_mult = await EventService(self.session).get_multiplier()
            multiplier *= event_mult

        total = points * multiplier
        user.points += total
        progress = await self._get_or_create_progress(user_id)
        progress.last_activity_at = datetime.datetime.utcnow()
        await self.session.commit()
        await self.session.refresh(progress)
        await self.session.refresh(user)
        level_service = LevelService(self.session)
        await level_service.check_for_level_up(user, bot=bot)

        ach_service = AchievementService(self.session)
        new_badges = await ach_service.check_user_badges(user_id)
        for badge in new_badges:
            await ach_service.award_badge(user_id, badge.id)
            if bot:
                await bot.send_message(
                    user_id,
                    f"🏅 Has obtenido la insignia {badge.icon or ''} {badge.name}!",
                )
        logger.info(
            f"User {user_id} gained {total} points (base {points}, x{multiplier}). Total: {user.points}"
        )
        if bot and user.points - progress.last_notified_points >= 5:
            await bot.send_message(
                user_id,
                f"Has acumulado {user.points:.1f} puntos en total",
            )
            progress.last_notified_points = user.points
            await self.session.commit()
        return progress

    async def deduct_points(self, user_id: int, points: int) -> User | None:
        user = await self.session.get(User, user_id)
        if user and user.points >= points:
            user.points -= points
            await self.session.commit()
            await self.session.refresh(user)
            logger.info(f"User {user_id} lost {points} points. Total: {user.points}")
            return user
        logger.warning(f"Failed to deduct {points} points from user {user_id}. Not enough points or user not found.")
        return None

    async def get_user_points(self, user_id: int) -> int:
        user = await self.session.get(User, user_id)
        return user.points if user else 0

    async def get_top_users(self, limit: int = 10) -> list[User]:
        """Return the top users ordered by points."""
        stmt = select(User).order_by(User.points.desc()).limit(limit)
        result = await self.session.execute(stmt)
        top_users = result.scalars().all()
        return top_users
