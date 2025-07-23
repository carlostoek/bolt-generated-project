from __future__ import annotations

from aiogram import Bot
from aiogram.types import Message, ReactionTypeEmoji
from aiogram.exceptions import (
    TelegramBadRequest,
    TelegramForbiddenError,
    TelegramAPIError,
)
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
import datetime
import logging

from .config_service import ConfigService
from .channel_service import ChannelService
from database.models import ButtonReaction
from keyboards.inline_post_kb import get_reaction_kb
from services.message_registry import store_message
from utils.config import VIP_CHANNEL_ID, FREE_CHANNEL_ID

logger = logging.getLogger(__name__)


class MessageService:
    def __init__(self, session: AsyncSession, bot: Bot):
        self.session = session
        self.bot = bot
        self.channel_service = ChannelService(self.session)

    async def send_interactive_post(
        self,
        text: str,
        channel_type: str = "vip",
    ) -> Message | bool | None:
        """Send a message with interactive buttons to the configured channel.

        Returns the ``Message`` object on success, ``None`` when the channel
        isn't configured and ``False`` if sending fails due to Telegram
        errors.
        """
        config = ConfigService(self.session)

        target_channel_id: int | str | None = None
        channel_type = channel_type.lower()
        if channel_type == "vip":
            target_channel_id = await config.get_vip_channel_id()
            if target_channel_id is None:
                target_channel_id = VIP_CHANNEL_ID
        elif channel_type == "free":
            target_channel_id = await config.get_free_channel_id()
            if target_channel_id is None:
                target_channel_id = FREE_CHANNEL_ID

        if not target_channel_id:
            logger.warning(f"No channel ID configured for type: {channel_type}")
            return None

        target_channel_id_str = str(target_channel_id)

        if not text or not text.strip():
            text = "\u00a1Un nuevo post interactivo! Reacciona para ganar puntos."

        try:
            raw_reactions, _ = await self.channel_service.get_reactions_and_points(target_channel_id)

            sent = await self.bot.send_message(
                chat_id=target_channel_id_str,
                text=text,
                reply_markup=None,
            )

            real_message_id = sent.message_id

            counts = await self.get_reaction_counts(real_message_id)

            updated_markup = get_reaction_kb(
                reactions=raw_reactions,
                current_counts=counts,
                message_id=real_message_id,
                channel_id=target_channel_id,
            )

            logger.info(f"DEBUG: Markup to edit: {updated_markup}")

            await self.bot.edit_message_reply_markup(
                chat_id=target_channel_id_str,
                message_id=real_message_id,
                reply_markup=updated_markup,
            )
            store_message(target_channel_id, real_message_id)

            if channel_type == "vip":
                vip_reactions = await config.get_vip_reactions()
                if vip_reactions:
                    try:
                        await self.bot.set_message_reaction(
                            chat_id=target_channel_id_str,
                            message_id=real_message_id,
                            reaction=[ReactionTypeEmoji(emoji=r) for r in vip_reactions[:10]],
                        )
                    except TelegramAPIError as e:
                        logger.error(
                            f"Error al establecer reacciones nativas en mensaje {real_message_id} del canal {target_channel_id}: {e}",
                            exc_info=True,
                        )

            from services.mission_service import MissionService
            mission_service = MissionService(self.session)
            await mission_service.create_mission(
                name=f"Reaccionar {real_message_id}",
                description="Reacciona a la publicaci\u00f3n para ganar puntos",
                mission_type="reaction",
                target_value=1,
                reward_points=1,
                duration_days=7,
                requires_action=True,
                action_data={"target_message_id": real_message_id},
            )
            return sent
        except (TelegramBadRequest, TelegramForbiddenError, TelegramAPIError) as e:
            logger.error(
                f"Failed to send interactive post to channel {target_channel_id}: {e}",
                exc_info=True,
            )
            return False

    async def register_reaction(
        self, user_id: int, message_id: int, reaction_type: str
    ) -> ButtonReaction | None:
        stmt = select(ButtonReaction).where(
            ButtonReaction.message_id == message_id,
            ButtonReaction.user_id == user_id,
        )
        result = await self.session.execute(stmt)
        if result.scalar():
            return None

        reaction = ButtonReaction(
            message_id=message_id,
            user_id=user_id,
            reaction_type=reaction_type,
        )
        self.session.add(reaction)
        await self.session.commit()
        await self.session.refresh(reaction)

        from services.mission_service import MissionService
        mission_service = MissionService(self.session)
        mission_id = f"reaction_reaccionar_{message_id}"
        await mission_service.complete_mission(
            user_id,
            mission_id,
            reaction_type=reaction_type,
            target_message_id=message_id,
            bot=self.bot,
        )
        from services.minigame_service import MiniGameService
        await MiniGameService(self.session).record_reaction(user_id, self.bot)

        return reaction

    async def get_reaction_counts(self, message_id: int) -> dict[str, int]:
        """Return reaction counts for the given message."""
        stmt = (
            select(ButtonReaction.reaction_type, func.count(ButtonReaction.id))
            .where(ButtonReaction.message_id == message_id)
            .group_by(ButtonReaction.reaction_type)
        )
        result = await self.session.execute(stmt)
        return {row[0]: row[1] for row in result.all()}

    async def update_reaction_markup(self, chat_id: int, message_id: int) -> None:
        """Update inline keyboard of an interactive post with current counts."""
        chat_id_str = str(chat_id)

        counts = await self.get_reaction_counts(message_id)

        raw_reactions, _ = await self.channel_service.get_reactions_and_points(chat_id)

        try:
            markup_to_edit = get_reaction_kb(
                reactions=raw_reactions,
                current_counts=counts,
                message_id=message_id,
                channel_id=chat_id,
            )
            logger.info(f"DEBUG: Markup being sent for update: {markup_to_edit}")

            await self.bot.edit_message_reply_markup(
                chat_id=chat_id_str,
                message_id=message_id,
                reply_markup=markup_to_edit,
            )
        except TelegramBadRequest as e:
            logger.error(
                f"Failed to update reaction markup for chat {chat_id}, message {message_id}: {e}",
                exc_info=True,
            )
        except TelegramAPIError as e:
            logger.error(
                f"Unexpected API error updating reaction markup for chat {chat_id}, message {message_id}: {e}",
                exc_info=True,
            )

    async def get_weekly_reaction_ranking(self, limit: int = 3) -> list[tuple[int, int]]:
        """Return a list of (user_id, count) for reactions in last 7 days."""
        since = datetime.datetime.utcnow() - datetime.timedelta(days=7)
        stmt = (
            select(ButtonReaction.user_id, func.count(ButtonReaction.id))
            .where(ButtonReaction.created_at >= since)
            .group_by(ButtonReaction.user_id)
            .order_by(func.count(ButtonReaction.id).desc())
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return result.all()
