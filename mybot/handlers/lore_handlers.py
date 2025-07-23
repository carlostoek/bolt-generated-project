"""Handlers para mostrar y gestionar las piezas de lore desbloqueadas."""

import logging
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from database.models import LorePiece, UserLorePiece


logger = logging.getLogger(__name__)

router = Router()


@router.message(Command("mochila"))
async def show_lore_backpack(message: Message, session: AsyncSession) -> None:
    """Muestra todas las pistas desbloqueadas por el usuario."""
    stmt = select(UserLorePiece).where(UserLorePiece.user_id == message.from_user.id)
    result = await session.execute(stmt)
    records = result.scalars().all()

    if not records:
        await message.answer("Aún no has desbloqueado ninguna pista.")
        return

    pieces = []
    for rec in records:
        piece = await session.get(LorePiece, rec.lore_piece_id)
        if piece:
            pieces.append(piece)

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=p.title, callback_data=f"show_lore_piece:{p.code_name}")]
            for p in pieces
        ]
    )

    await message.answer(
        "Aquí están las pistas que has descubierto hasta ahora en tu mochila:",
        reply_markup=keyboard,
    )


@router.callback_query(F.data.startswith("show_lore_piece:"))
async def show_lore_piece(callback: CallbackQuery, session: AsyncSession) -> None:
    """Envía el contenido de una pista al usuario."""
    code = callback.data.split(":", 1)[1]
    stmt = select(LorePiece).where(LorePiece.code_name == code)
    result = await session.execute(stmt)
    piece = result.scalar_one_or_none()

    if not piece:
        await callback.answer("Pista no encontrada", show_alert=True)
        return

    try:
        if piece.content_type == "text":
            await callback.message.answer(piece.content)
        elif piece.content_type == "image":
            await callback.message.answer_photo(piece.content)
        elif piece.content_type == "video":
            await callback.message.answer_video(piece.content)
        else:
            await callback.message.answer(piece.content)
    except Exception as exc:
        logger.error("Error sending lore piece %s: %s", code, exc)
        await callback.answer("No se pudo mostrar la pista", show_alert=True)
        return

    await callback.answer()
