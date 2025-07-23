import logging

from aiogram import Router, F, Bot
from aiogram.types import CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession

from services.message_service import MessageService
from services.channel_service import ChannelService
from services.message_registry import validate_message
from utils.messages import BOT_MESSAGES

router = Router()
logger = logging.getLogger(__name__)


@router.callback_query(F.data.startswith("ip_"))
async def handle_reaction_callback(
    callback: CallbackQuery, session: AsyncSession, bot: Bot
) -> None:
    parts = callback.data.split("_")
    if len(parts) < 4:
        return await callback.answer()

    try:
        channel_id = int(parts[1])
    except ValueError:
        channel_id = parts[1]

    try:
        message_id = int(parts[2])
    except ValueError:
        return await callback.answer()

    reaction_type = parts[3]

    if not callback.message:
        return await callback.answer()

    chat_id = callback.message.chat.id
    valid = validate_message(chat_id, message_id)
    logger.info(
        "Edit attempt chat_id=%s message_id=%s valid=%s", chat_id, message_id, valid
    )

    if not valid:
        logger.warning(
            "[ERROR] El mensaje que se intenta editar no fue enviado por este bot o el chat_id es incorrecto."
        )
        return await callback.answer()

    service = MessageService(session, bot)
    channel_service = ChannelService(session)

    reaction_result = await service.register_reaction(
        callback.from_user.id,
        message_id,
        reaction_type,
    )

    if reaction_result is None:
        await callback.answer(
            BOT_MESSAGES.get("reaction_already", "Ya has reaccionado a este post."),
            show_alert=True,
        )
        return

    from services.point_service import PointService

    points_dict = await channel_service.get_reaction_points(channel_id)
    points = float(points_dict.get(reaction_type, 0.0))

    await PointService(session).add_points(callback.from_user.id, points, bot=bot)
    from services.mission_service import MissionService
    mission_service = MissionService(session)
    await mission_service.update_progress(callback.from_user.id, "reaction", bot=bot)

    await service.update_reaction_markup(chat_id, message_id)
    await callback.answer(BOT_MESSAGES["reaction_registered_points"].format(points=points))
    await bot.send_message(
        callback.from_user.id,
        BOT_MESSAGES["reaction_registered_points"].format(points=points),
    )
