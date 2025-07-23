from aiogram import Router, F, Bot
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession
from services.daily_gift_service import DailyGiftService
from services.config_service import ConfigService
from utils.messages import BOT_MESSAGES

router = Router()

@router.message(F.text.regexp("/dailygift"))
async def claim_daily_gift(message: Message, session: AsyncSession, bot: Bot):
    config = ConfigService(session)
    if (await config.get_value("daily_gift_enabled")) == "false":
        await message.answer(BOT_MESSAGES.get("daily_gift_disabled", "Regalos diarios deshabilitados."))
        return
    service = DailyGiftService(session)
    claimed, points = await service.claim_gift(message.from_user.id, bot)
    if claimed:
        await message.answer(BOT_MESSAGES.get("daily_gift_received", "Has recibido {points} puntos").format(points=points))
    else:
        await message.answer(BOT_MESSAGES.get("daily_gift_already", "Ya reclamaste el regalo diario."))
