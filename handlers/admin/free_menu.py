from aiogram import Router, F
from aiogram.types import CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession
from utils.user_roles import is_admin
from utils.menu_utils import update_menu
from keyboards.common import get_back_kb
from keyboards.free_channel_admin_kb import get_free_channel_admin_kb

router = Router()


@router.callback_query(F.data == "admin_free")
async def free_menu(callback: CallbackQuery, session: AsyncSession):
    """Free channel admin menu."""
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer()
    # TODO: Implement logic to check if channel is configured
    channel_configured = True  # Placeholder for now
    await update_menu(
        callback,
        "Men\u00fa de Administraci\u00f3n de Canal Gratuito",
        get_free_channel_admin_kb(channel_configured=channel_configured),
        session,
        "admin_free",
    )
    await callback.answer()
