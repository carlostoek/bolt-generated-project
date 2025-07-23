from datetime import datetime, timedelta
from aiogram import Router, Bot
from aiogram.filters import CommandStart
from aiogram.types import Message
from aiogram.filters.command import CommandObject
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import User
from utils.text_utils import sanitize_text
from services.token_service import TokenService
from services.subscription_service import SubscriptionService
from utils.menu_utils import send_temporary_reply
from utils.messages import BOT_MESSAGES
from services.achievement_service import AchievementService
from services.config_service import ConfigService
from utils.user_roles import clear_role_cache
import logging

logger = logging.getLogger(__name__)
router = Router()


@router.message(CommandStart(deep_link=True))
async def start_with_token(message: Message, command: CommandObject, session: AsyncSession, bot: Bot):
    token_string = command.args
    if not token_string:
        logger.warning("Deep link start without token")
        return

    user_id = message.from_user.id
    logger.info(f"User {user_id} attempting to activate token: {token_string}")

    # Clear role cache to ensure fresh role detection after activation
    clear_role_cache(user_id)

    service = TokenService(session)
    try:
        duration = await service.activate_token(token_string, user_id)
        logger.info(f"Token {token_string} activated successfully for user {user_id}, duration: {duration} days")
    except Exception as e:
        logger.error(f"Token activation failed for user {user_id}: {e}")
        await send_temporary_reply(message, "❌ Token inválido o ya utilizado.")
        return

    # Get or create user
    user = await session.get(User, user_id)
    if not user:
        user = User(
            id=user_id,
            username=sanitize_text(message.from_user.username),
            first_name=sanitize_text(message.from_user.first_name),
            last_name=sanitize_text(message.from_user.last_name),
        )
        session.add(user)
        logger.info(f"Created new user: {user_id}")

    # Set VIP role and expiration
    user.role = "vip"
    expires_at = datetime.utcnow() + timedelta(days=duration)
    user.vip_expires_at = expires_at
    user.last_reminder_sent_at = None

    # Record the subscription for tracking
    sub_service = SubscriptionService(session)
    existing = await sub_service.get_subscription(user.id)
    if existing:
        existing.expires_at = expires_at
        logger.info(f"Updated existing subscription for user {user_id}")
    else:
        await sub_service.create_subscription(user.id, expires_at)
        logger.info(f"Created new subscription for user {user_id}")

    await session.commit()

    # Grant VIP achievement
    ach_service = AchievementService(session)
    await ach_service.check_vip_achievement(user.id, bot=bot)

    # Generate VIP channel invite link
    invite_link = None
    config_service = ConfigService(session)
    vip_id = await config_service.get_vip_channel_id()
    
    if vip_id:
        try:
            # Create a single-use invite link
            link = await bot.create_chat_invite_link(
                vip_id, 
                member_limit=1,
                expire_date=datetime.utcnow() + timedelta(hours=24)  # Link expires in 24 hours
            )
            invite_link = link.invite_link
            logger.info(f"Generated VIP invite link for user {user_id}")
        except Exception as e:
            logger.error(f"Failed to create VIP invite link: {e}")
            invite_link = None

    # Send special welcome message from Señorita Kinky
    await message.answer(BOT_MESSAGES["vip_welcome_special"])

    if invite_link:
        butler_msg = BOT_MESSAGES["vip_activation_details"].format(
            duration=duration,
            expires_at=expires_at.strftime("%d/%m/%Y %H:%M"),
            invite_link=invite_link,
        )
    else:
        butler_msg = BOT_MESSAGES["vip_activation_no_link"].format(
            duration=duration,
            expires_at=expires_at.strftime("%d/%m/%Y %H:%M"),
        )

    await message.answer(butler_msg)
    logger.info(f"VIP activation completed for user {user_id}")

    # Clear role cache again to ensure the new role is detected immediately
    clear_role_cache(user_id)
