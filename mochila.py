from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from sqlalchemy.future import select
from database.models import UserLorePiece, LorePiece
from database.setup import get_session

router = Router()

@router.message(F.text == "🎒 Mochila")
async def mostrar_mochila(message: Message):
    session_factory = await get_session()
    async with session_factory() as session:
        user_id = message.from_user.id

        result = await session.execute(
            select(LorePiece)
            .join(UserLorePiece, LorePiece.id == UserLorePiece.lore_piece_id)
            .where(UserLorePiece.user_id == user_id)
        )

        pistas = result.scalars().all()
        if not pistas:
            await message.answer("Tu mochila está vacía.")
            return

        botones = [
            [InlineKeyboardButton(pista.title, callback_data=f"ver_pista:{pista.id}")]
            for pista in pistas
        ]

        await message.answer("🎒 Estas son tus pistas:", reply_markup=InlineKeyboardMarkup(inline_keyboard=botones))

@router.callback_query(F.data.startswith("ver_pista:"))
async def ver_pista(callback: CallbackQuery):
    session_factory = await get_session()
    async with session_factory() as session:
        pista_id = int(callback.data.split(":")[1])

        pista = await session.get(LorePiece, pista_id)
        if pista.content_type == "image":
            await callback.message.answer_photo(pista.content, caption=pista.title)
        elif pista.content_type == "video":
            await callback.message.answer_video(pista.content, caption=pista.title)
        else:
            await callback.message.answer(f"📜 {pista.title}\n\n{pista.content}")

        await callback.answer()
