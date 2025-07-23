import datetime
from aiogram import Bot
from sqlalchemy.ext.asyncio import AsyncSession
from database.models import UserStats
from .point_service import PointService
from .config_service import ConfigService

class DailyGiftService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.point_service = PointService(session)
        self.config_service = ConfigService(session)

    async def claim_gift(self, user_id: int, bot: Bot) -> tuple[bool, int]:
        """Attempt to claim the daily gift. Returns (claimed, points_awarded)."""
        progress = await self.session.get(UserStats, user_id)
        if not progress:
            progress = UserStats(user_id=user_id)
            self.session.add(progress)
            await self.session.commit()
        now = datetime.datetime.utcnow()
        if progress.last_daily_gift_at and (now - progress.last_daily_gift_at).total_seconds() < 86400:
            return False, 0
        amount_str = await self.config_service.get_value("daily_gift_points")
        try:
            points = int(amount_str) if amount_str else 5
        except Exception:
            points = 5
        await self.point_service.add_points(user_id, points, bot=bot)
        progress.last_daily_gift_at = now
        await self.session.commit()
        return True, points
