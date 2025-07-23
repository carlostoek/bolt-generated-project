from __future__ import annotations

from datetime import datetime, timedelta
from secrets import token_urlsafe
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from database.models import InviteToken, SubscriptionToken, Token, Tariff, User, VipSubscription
from services.achievement_service import AchievementService
from services.subscription_service import SubscriptionService
from aiogram import Bot
import logging

logger = logging.getLogger(__name__)


class TokenService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_token(self, created_by: int, expires_in: int | None = None) -> InviteToken:
        token = token_urlsafe(16)
        expires_at = datetime.utcnow() + timedelta(seconds=expires_in) if expires_in else None
        obj = InviteToken(token=token, created_by=created_by, expires_at=expires_at)
        self.session.add(obj)
        await self.session.commit()
        await self.session.refresh(obj)
        return obj

    async def activate_token(self, token_string: str, user_id: int) -> int:
        """Activate a VIP token and return the duration in days."""
        stmt = select(Token).where(Token.token_string == token_string, Token.is_used == False)
        result = await self.session.execute(stmt)
        token = result.scalar_one_or_none()
        
        if not token:
            logger.warning(f"Token activation failed: Token {token_string} not found or already used")
            raise ValueError("Token inválido o ya utilizado")
        
        tariff = await self.session.get(Tariff, token.tariff_id)
        if not tariff:
            logger.error(f"Token activation failed: Tariff {token.tariff_id} not found")
            raise ValueError("Tarifa no encontrada")
        
        # Mark token as used
        token.is_used = True
        token.user_id = user_id
        token.activated_at = datetime.utcnow()
        
        logger.info(f"Token {token_string} activated by user {user_id} for {tariff.duration_days} days")
        await self.session.commit()
        return tariff.duration_days

    async def use_token(self, token: str, user_id: int, *, bot: Bot | None = None) -> bool:
        stmt = select(InviteToken).where(InviteToken.token == token)
        result = await self.session.execute(stmt)
        obj = result.scalar_one_or_none()
        if not obj or obj.used_by or (obj.expires_at and obj.expires_at < datetime.utcnow()):
            return False
        obj.used_by = user_id
        obj.used_at = datetime.utcnow()
        await self.session.commit()
        ach_service = AchievementService(self.session)
        await ach_service.check_invite_achievements(obj.created_by, bot=bot)
        return True

    async def create_subscription_token(self, plan_id: int, created_by: int) -> SubscriptionToken:
        token = token_urlsafe(8)
        obj = SubscriptionToken(token=token, plan_id=plan_id, created_by=created_by)
        self.session.add(obj)
        await self.session.commit()
        await self.session.refresh(obj)
        return obj

    async def redeem_subscription_token(self, token: str, user_id: int) -> SubscriptionToken | None:
        stmt = select(SubscriptionToken).where(SubscriptionToken.token == token)
        result = await self.session.execute(stmt)
        obj = result.scalar_one_or_none()
        if not obj or obj.used_by:
            return None
        obj.used_by = user_id
        obj.used_at = datetime.utcnow()
        await self.session.commit()
        return obj

    async def create_vip_token(self, tariff_id: int) -> Token:
        """Create a VIP subscription token for the given tariff."""
        token_str = token_urlsafe(16)
        obj = Token(token_string=token_str, tariff_id=tariff_id)
        self.session.add(obj)
        await self.session.commit()
        await self.session.refresh(obj)
        logger.info(f"VIP token created: {token_str} for tariff {tariff_id}")
        return obj

    async def invalidate_vip_token(self, token_string: str) -> bool:
        """Remove an unused VIP token so it can no longer be redeemed."""
        stmt = select(Token).where(Token.token_string == token_string, Token.is_used == False)
        result = await self.session.execute(stmt)
        obj = result.scalar_one_or_none()
        if not obj:
            return False
        await self.session.delete(obj)
        await self.session.commit()
        logger.info(f"VIP token invalidated: {token_string}")
        return True

    async def get_token_info(self, token_string: str) -> Token | None:
        """Get token information without activating it."""
        stmt = select(Token).where(Token.token_string == token_string)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()


async def validate_token(token: str, session: AsyncSession) -> str | None:
    """Validate a legacy VIP activation token and mark it as used."""
    stmt = select(Token).where(Token.token_string == token)
    result = await session.execute(stmt)
    obj = result.scalar_one_or_none()
    if not obj or obj.is_used:
        return None
    tariff = await session.get(Tariff, obj.tariff_id)
    if not tariff:
        return None
    obj.is_used = True
    await session.commit()
    return tariff.duration_days
