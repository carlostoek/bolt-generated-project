from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from sqlalchemy.ext.asyncio import AsyncSession
from services.config_service import ConfigService
from services.point_service import PointService
from utils.messages import BOT_MESSAGES
import random

router = Router()

@router.message(F.text.regexp("/ruleta"))
async def play_roulette(message: Message, session: AsyncSession, bot: Bot):
    config = ConfigService(session)
    if (await config.get_value("minigames_enabled")) == "false":
        await message.answer(BOT_MESSAGES.get("minigames_disabled", "Minijuegos deshabilitados."))
        return
    from services.minigame_service import MiniGameService
    service = MiniGameService(session)
    score = await service.play_roulette(message.from_user.id, bot)
    await message.answer(BOT_MESSAGES.get("dice_points", "Ganaste {points} puntos").format(points=score))

@router.message(F.text.regexp("/reto"))
async def start_reaction_challenge(message: Message, session: AsyncSession, bot: Bot):
    config = ConfigService(session)
    if (await config.get_value("minigames_enabled")) == "false":
        await message.answer(BOT_MESSAGES.get("minigames_disabled", "Minijuegos deshabilitados."))
        return
    from services.minigame_service import MiniGameService
    service = MiniGameService(session)
    challenge = await service.start_reaction_challenge(message.from_user.id, reactions=3)
    await message.answer(
        BOT_MESSAGES.get("challenge_started", "¡Reto iniciado! Reacciona a {count} publicaciones en pocos minutos.").format(count=challenge.target_reactions)
    )

TRIVIA = [
    {
        "q": "¿Capital de Francia?",
        "opts": ["Madrid", "París", "Roma"],
        "answer": 1,
    },
    {
        "q": "¿Cuántos días tiene una semana?",
        "opts": ["5", "7", "10"],
        "answer": 1,
    },
    {
        "q": "¿Color resultante de mezclar rojo y azul?",
        "opts": ["Verde", "Morado", "Amarillo"],
        "answer": 1,
    },
]

@router.message(F.text.regexp("/dice"))
async def play_dice(message: Message, session: AsyncSession, bot: Bot):
    config = ConfigService(session)
    if (await config.get_value("minigames_enabled")) == "false":
        await message.answer(BOT_MESSAGES.get("minigames_disabled", "Minijuegos deshabilitados."))
        return
    dice_msg = await bot.send_dice(message.chat.id)
    score = dice_msg.dice.value
    await PointService(session).add_points(message.from_user.id, score, bot=bot)
    await message.answer(BOT_MESSAGES.get("dice_points", "Ganaste {points} puntos").format(points=score))

@router.message(F.text.regexp("/trivia"))
async def send_trivia(message: Message, session: AsyncSession):
    config = ConfigService(session)
    if (await config.get_value("minigames_enabled")) == "false":
        await message.answer(BOT_MESSAGES.get("minigames_disabled", "Minijuegos deshabilitados."))
        return
    q = random.choice(TRIVIA)
    buttons = [
        [InlineKeyboardButton(text=opt, callback_data="trivia_correct" if i==q["answer"] else "trivia_wrong")]
        for i, opt in enumerate(q["opts"])
    ]
    await message.answer(q["q"], reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))

@router.callback_query(F.data.in_({"trivia_correct", "trivia_wrong"}))
async def trivia_answer(callback: CallbackQuery, session: AsyncSession, bot: Bot):
    config = ConfigService(session)
    if (await config.get_value("minigames_enabled")) == "false":
        return await callback.answer(BOT_MESSAGES.get("minigames_disabled", "Minijuegos deshabilitados."), show_alert=True)
    if callback.data == "trivia_correct":
        await PointService(session).add_points(callback.from_user.id, 5, bot=bot)
        await callback.message.edit_text(BOT_MESSAGES.get("trivia_correct", "¡Correcto! +5 puntos"))
    else:
        await callback.message.edit_text(BOT_MESSAGES.get("trivia_wrong", "Respuesta incorrecta."))
    await callback.answer()
