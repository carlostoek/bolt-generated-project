import logging
from aiogram import Router, Bot, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery

from utils.config import Config
from utils.user_roles import is_admin
from keyboards.publication_test_kb import (
    get_publication_test_kb,
    get_publication_test_completed_kb,
)

router = Router()
logger = logging.getLogger(__name__)


@router.message(Command("test_publicacion"))
async def cmd_test_publicacion(message: Message, bot: Bot) -> None:
    """Send a test message to the configured channel to check publication mode."""
    if not await is_admin(message.from_user.id):
        return

    channel_id = Config.CHANNEL_ID
    logger.info(
        "Enviando mensaje de test_publicacion al canal %s por solicitud de %s",
        channel_id,
        message.from_user.id,
    )

    await bot.send_message(
        chat_id=channel_id,
        text="\U0001F9EA Test de publicación desde el bot. Pulsa el botón para confirmar.",
        reply_markup=get_publication_test_kb(),
    )
    await message.answer("Mensaje de prueba enviado al canal.")


@router.callback_query(F.data == "confirmar_test_publicacion")
async def cb_confirmar_test(callback: CallbackQuery, bot: Bot) -> None:
    """Handle confirmation of the publication test."""
    logger.info(
        "Confirmación de test_publicacion recibida de usuario %s", callback.from_user.id
    )
    text = (
        f"{callback.message.text}\n\n\u2714\uFE0F Confirmado"
        if callback.message and callback.message.text
        else "\u2714\uFE0F Confirmado"
    )
    await bot.edit_message_text(
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id,
        text=text,
        reply_markup=get_publication_test_completed_kb(),
    )
    await callback.answer("Test confirmado")
