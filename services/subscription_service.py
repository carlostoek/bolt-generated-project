from __future__ import annotations

from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from aiogram import Bot

from services.config_service import ConfigService

from database.models import VipSubscription, User, Token, Tariff
import logging

logger = logging.getLogger(__name__)


class SubscriptionService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_subscription(self, user_id: int) -> VipSubscription | None:
        stmt = select(VipSubscription).where(VipSubscription.user_id == user_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def create_subscription(
        self, user_id: int, expires_at: datetime | None = None
    ) -> VipSubscription:
        sub = VipSubscription(user_id=user_id, expires_at=expires_at)
        self.session.add(sub)
        await self.session.commit()
        await self.session.refresh(sub)
        logger.info(f"Created VIP subscription for user {user_id}, expires: {expires_at}")
        return sub

    async def get_statistics(self) -> tuple[int, int, int]:
        """Return total, active and expired subscription counts."""
        now = datetime.utcnow()

        total_stmt = select(func.count()).select_from(VipSubscription)
        active_stmt = (
            select(func.count())
            .select_from(VipSubscription)
            .where(
                (VipSubscription.expires_at.is_(None))
                | (VipSubscription.expires_at > now)
            )
        )
        expired_stmt = (
            select(func.count())
            .select_from(VipSubscription)
            .where(
                VipSubscription.expires_at.is_not(None),
                VipSubscription.expires_at <= now,
            )
        )

        total_res = await self.session.execute(total_stmt)
        active_res = await self.session.execute(active_stmt)
        expired_res = await self.session.execute(expired_stmt)

        return (
            total_res.scalar() or 0,
            active_res.scalar() or 0,
            expired_res.scalar() or 0,
        )

    async def get_active_subscribers(self) -> list[VipSubscription]:
        """Return list of currently active subscriptions."""
        now = datetime.utcnow()
        stmt = select(VipSubscription).where(
            (VipSubscription.expires_at.is_(None)) | (VipSubscription.expires_at > now)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def extend_subscription(self, user_id: int, days: int) -> VipSubscription:
        """Extend an existing subscription or create one if missing."""
        from datetime import timedelta

        now = datetime.utcnow()
        sub = await self.get_subscription(user_id)
        new_exp = now + timedelta(days=days)
        
        if sub:
            if sub.expires_at and sub.expires_at > now:
                sub.expires_at = sub.expires_at + timedelta(days=days)
            else:
                sub.expires_at = new_exp
        else:
            sub = VipSubscription(user_id=user_id, expires_at=new_exp)
            self.session.add(sub)

        # Update user record as well
        user = await self.session.get(User, user_id)
        if user:
            user.role = "vip"
            if user.vip_expires_at and user.vip_expires_at > now:
                user.vip_expires_at = user.vip_expires_at + timedelta(days=days)
            else:
                user.vip_expires_at = new_exp
            user.last_reminder_sent_at = None

        await self.session.commit()
        logger.info(f"Extended VIP subscription for user {user_id} by {days} days")
        return sub

    async def revoke_subscription(self, user_id: int, *, bot: Bot | None = None) -> None:
        """Immediately expire a user's subscription and optionally kick from the VIP channel."""
        now = datetime.utcnow()
        sub = await self.get_subscription(user_id)
        if sub:
            sub.expires_at = now

        user = await self.session.get(User, user_id)
        if user:
            user.role = "free"
            user.vip_expires_at = None

        if bot:
            config_service = ConfigService(self.session)
            vip_channel_id = await config_service.get_vip_channel_id()
            if vip_channel_id:
                try:
                    await bot.ban_chat_member(vip_channel_id, user_id)
                    await bot.unban_chat_member(vip_channel_id, user_id)
                except Exception as e:
                    logger.exception("Failed to remove %s from VIP channel: %s", user_id, e)

        await self.session.commit()
        logger.info(f"Revoked VIP subscription for user {user_id}")

    async def set_subscription_expiration(
        self, user_id: int, expires_at: datetime | None
    ) -> VipSubscription:
        """Set or create subscription with specific expiration date."""
        sub = await self.get_subscription(user_id)
        if sub:
            sub.expires_at = expires_at
        else:
            sub = VipSubscription(user_id=user_id, expires_at=expires_at)
            self.session.add(sub)

        user = await self.session.get(User, user_id)
        if user:
            if expires_at is None or expires_at > datetime.utcnow():
                user.role = "vip"
                user.vip_expires_at = expires_at
                user.last_reminder_sent_at = None
            else:
                user.role = "free"
                user.vip_expires_at = expires_at

        await self.session.commit()
        logger.info(
            "Set VIP expiration for user %s to %s", user_id, expires_at
        )
        return sub

    async def is_subscription_active(self, user_id: int) -> bool:
        """Check if user has an active VIP subscription."""
        sub = await self.get_subscription(user_id)
        if not sub:
            return False
        
        if sub.expires_at is None:
            return True
        
        return sub.expires_at > datetime.utcnow()


async def get_admin_statistics(session: AsyncSession) -> dict:
    """Return statistics for the admin panel."""

    sub_service = SubscriptionService(session)
    total_subs, active_subs, expired_subs = await sub_service.get_statistics()

    user_count_stmt = select(func.count()).select_from(User)
    user_count_res = await session.execute(user_count_stmt)
    total_users = user_count_res.scalar() or 0

    # Calculate revenue from used tokens
    revenue_stmt = (
        select(func.sum(Tariff.price))
        .select_from(Token)
        .join(Tariff, Token.tariff_id == Tariff.id)
        .where(Token.is_used.is_(True))
    )
    revenue_res = await session.execute(revenue_stmt)
    total_revenue = revenue_res.scalar() or 0

    return {
        "subscriptions_total": total_subs,
        "subscriptions_active": active_subs,
        "subscriptions_expired": expired_subs,
        "users_total": total_users,
        "revenue_total": total_revenue,
    }
