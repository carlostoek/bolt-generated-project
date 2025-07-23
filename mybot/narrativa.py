from aiogram import Bot
from sqlalchemy.future import select
from database.models import UserLorePiece, LorePiece
from database.setup import get_session

async def desbloquear_pista(bot: Bot, user_id: int, pista_code: str):
    session_factory = await get_session()
    async with session_factory() as session:

        pista = await session.execute(select(LorePiece).where(LorePiece.code_name == pista_code))
        pista = pista.scalar_one_or_none()

        if not pista:
            return

        existente = await session.execute(
            select(UserLorePiece)
            .where(UserLorePiece.user_id == user_id, UserLorePiece.lore_piece_id == pista.id)
        )
        if existente.scalar_one_or_none():
            return

        user_pista = UserLorePiece(user_id=user_id, lore_piece_id=pista.id)
        session.add(user_pista)
        await session.commit()

        if pista.content_type == "image":
            await bot.send_photo(user_id, pista.content, caption=f"\ud83d\udcd6 {pista.title}")
        elif pista.content_type == "video":
            await bot.send_video(user_id, pista.content, caption=f"\ud83d\udcd6 {pista.title}")
        else:
            await bot.send_message(user_id, f"\ud83d\udcd6 {pista.title}\n\n{pista.content}")
