from __future__ import annotations

import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Union

from database.models import Channel
from utils.text_utils import sanitize_text
from utils.config import DEFAULT_REACTION_BUTTONS

logger = logging.getLogger(__name__)


class ChannelService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def add_channel(self, chat_id: int, title: str | None = None) -> Channel:
        channel = await self.session.get(Channel, chat_id)
        clean_title = sanitize_text(title) if title is not None else None
        if channel:
            if clean_title:
                channel.title = clean_title
        else:
            channel = Channel(id=chat_id, title=clean_title)
            self.session.add(channel)
        await self.session.commit()
        await self.session.refresh(channel)
        return channel

    async def list_channels(self) -> list[Channel]:
        result = await self.session.execute(select(Channel))
        return list(result.scalars().all())

    async def remove_channel(self, chat_id: int) -> None:
        channel = await self.session.get(Channel, chat_id)
        if channel:
            await self.session.delete(channel)
            await self.session.commit()

    async def set_reactions(
        self,
        chat_id: Union[int, str],
        reactions: list[str],
        reaction_points: dict[str, float] | None = None,
    ) -> Channel | None:
        """Configure emojis and their points for a given channel."""
        try:
            channel_id_int = int(chat_id)
        except ValueError:
            logger.error(
                "Invalid chat_id '%s' provided for set_reactions, cannot convert to int.",
                chat_id,
            )
            return None

        channel = await self.session.get(Channel, channel_id_int)
        new_channel: Channel | None = None
        if channel:
            channel.reactions = reactions

            if reaction_points is not None:
                channel.reaction_points = reaction_points
            elif not channel.reaction_points:
                channel.reaction_points = {}
            self.session.add(channel)
        else:
            new_channel = Channel(
                id=channel_id_int,
                title=f"Canal ID {channel_id_int}",
                reactions=reactions,
                reaction_points=reaction_points or {},
            )
            self.session.add(new_channel)

        await self.session.commit()
        await self.session.refresh(channel or new_channel)
        logger.info(
            "Reacciones actualizadas para el canal %s: %s, Puntos: %s",
            channel_id_int,
            reactions,
            reaction_points,
        )
        return channel or new_channel

    async def get_reactions_and_points(
        self, chat_id: Union[int, str]
    ) -> tuple[list[str], dict[str, float]]:
        """Return configured reactions and points for a channel."""
        try:
            channel_id_int = int(chat_id)
        except ValueError:
            logger.error(
                "Invalid chat_id '%s' provided, cannot convert to int.", chat_id
            )
            return DEFAULT_REACTION_BUTTONS, {
                r: 0.5 for r in DEFAULT_REACTION_BUTTONS
            }

        channel = await self.session.get(Channel, channel_id_int)

        configured_reactions: list[str] = []
        configured_points: dict[str, float] = {}

        if channel:
            if channel.reactions and isinstance(channel.reactions, list):
                configured_reactions = [
                    r for r in channel.reactions if isinstance(r, str)
                ][:10]

            if channel.reaction_points and isinstance(channel.reaction_points, dict):
                configured_points = {
                    k: float(v)
                    for k, v in channel.reaction_points.items()
                    if isinstance(v, (int, float))
                }

        if not configured_reactions:
            configured_reactions = DEFAULT_REACTION_BUTTONS

        final_points = {
            emoji: configured_points.get(emoji, 0.5)
            for emoji in configured_reactions
        }

        logger.debug(
            "Reacciones y puntos obtenidos para canal %s: Reacciones=%s, Puntos=%s",
            chat_id,
            configured_reactions,
            final_points,
        )
        return configured_reactions, final_points

    async def get_reaction_points(self, chat_id: int) -> dict[str, float]:
        """Return only reaction points for a channel."""
        _, points = await self.get_reactions_and_points(chat_id)
        return points
