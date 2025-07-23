from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram import Bot
from aiogram.filters import Command
from sqlalchemy.ext.asyncio import AsyncSession  # Importar AsyncSession

from keyboards.admin_kb import get_admin_kb
from utils.user_roles import is_admin
from services.scheduler import run_channel_request_check, run_vip_subscription_check

router = Router()


@router.message(Command("admin_menu"))
async def admin_menu(message: Message, session: AsyncSession):  # Agregar session
    if not await is_admin(message.from_user.id, session):  # Usar session
        return
    await message.answer("Menú de administración", reply_markup=get_admin_kb())


@router.callback_query(F.data == "admin_button")
async def admin_placeholder_handler(callback: CallbackQuery, session: AsyncSession):  # Agregar session
    # Ejemplo de uso de session
    # async with session.begin():
    #     result = await session.execute("SELECT 1")
    await callback.answer("Acción de administración")


@router.message(Command("run_schedulers"))
async def run_schedulers(
    message: Message, 
    bot: Bot,
    session: AsyncSession  # Inyectar sesión directamente
):
    """Permite a un admin ejecutar manualmente los schedulers"""
    if not await is_admin(message.from_user.id, session):  # Usar session
        return
    
    # Usar la sesión inyectada directamente
    await run_channel_request_check(bot, session)
    await run_vip_subscription_check(bot, session)
    await message.answer("Schedulers ejecutados")
