from aiogram import BaseMiddleware, Bot
from aiogram.types import Message, PollAnswer, ChatMemberUpdated
try:
    from aiogram.types import MessageReactionUpdated
except ImportError:  # Fallback for older aiogram
    MessageReactionUpdated = object
from sqlalchemy.ext.asyncio import AsyncSession
from database.models import User
from services.point_service import PointService
from utils.messages import BOT_MESSAGES
import logging
import datetime
from utils.user_roles import is_admin # Added import

logger = logging.getLogger(__name__)


class PointsMiddleware(BaseMiddleware):
    async def __call__(self, handler, event, data):
        session: AsyncSession = data.get("session")
        bot: Bot = data.get("bot")
        if not session or not bot:
            return await handler(event, data)

        # Verificar si es admin (usando la sesión)
        if session and hasattr(event, 'from_user') and event.from_user:
            if await is_admin(event.from_user.id, session):
                return await handler(event, data)

        service = PointService(session)
        from services.mission_service import MissionService
        mission_service = MissionService(session)

        try:
            if isinstance(event, Message):
                if event.from_user and not event.from_user.is_bot:
                    # Ignore bot commands so /start and similar messages don't
                    # grant points and trigger notifications
                    if event.text and event.text.startswith("/"):
                        return await handler(event, data)

                    await service.award_message(event.from_user.id, bot)
                    await mission_service.update_progress(event.from_user.id, "messages", bot=bot)
                    completed = await mission_service.increment_challenge_progress(
                        event.from_user.id,
                        "messages",
                        bot=bot,
                    )
                    for ch in completed:
                        await bot.send_message(
                            event.from_user.id,
                            BOT_MESSAGES["challenge_completed"].format(
                                challenge_type=ch.type,
                                points=100,
                            ),
                        )
            elif isinstance(event, MessageReactionUpdated):
                user_id = getattr(event, "user", None)
                if hasattr(user_id, "id"):
                    user_id = user_id.id
                message_id = getattr(event, "message_id", None)
                if user_id and message_id:
                    user = await session.get(User, user_id)
                    if not user:
                        user = User(id=user_id)
                        session.add(user)
                        await session.commit()
                    await service.award_reaction(user, message_id, bot)
                    await mission_service.update_progress(user_id, "reaction", bot=bot)
                    await bot.send_message(user_id, BOT_MESSAGES["reaction_registered"])
                    completed = await mission_service.increment_challenge_progress(
                        user_id,
                        "reactions",
                        bot=bot,
                    )
                    for ch in completed:
                        await bot.send_message(
                            user_id,
                            BOT_MESSAGES["challenge_completed"].format(
                                challenge_type=ch.type,
                                points=100,
                            ),
                        )
            elif isinstance(event, PollAnswer):
                await service.award_poll(event.user.id, bot)
            elif isinstance(event, ChatMemberUpdated):
                pass
        except Exception as e:
            logger.exception("Error awarding points: %s", e)
        return await handler(event, data)
