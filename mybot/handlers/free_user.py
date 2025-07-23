import logging
import asyncio
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession

from utils.user_roles import get_user_role
from utils.menu_manager import menu_manager
from keyboards.subscription_kb import get_free_main_menu_kb, get_vip_explore_kb
from keyboards.packs_kb import get_packs_list_kb, get_pack_detail_kb
from utils.messages import BOT_MESSAGES
from utils.keyboard_utils import get_back_keyboard
from utils.notify_admins import notify_admins

router = Router()
logger = logging.getLogger(__name__)


@router.message(Command("subscribe"))
async def show_free_main_menu(message: Message, session: AsyncSession):
    """Display the menu for free users."""
    if await get_user_role(message.bot, message.from_user.id, session=session) != "free":
        return

    await menu_manager.show_menu(
        message,
        BOT_MESSAGES.get("FREE_MENU_TEXT", "Menú gratuito"),
        get_free_main_menu_kb(),
        session,
        "free_main",
        delete_origin_message=True,
    )


@router.callback_query(F.data == "free_main_menu")
async def cb_free_main_menu(callback: CallbackQuery, session: AsyncSession):
    await menu_manager.update_menu(
        callback,
        BOT_MESSAGES.get("FREE_MENU_TEXT", "Menú gratuito"),
        get_free_main_menu_kb(),
        session,
        "free_main",
    )
    await callback.answer()


@router.callback_query(F.data == "free_gift")
async def cb_free_gift(callback: CallbackQuery, session: AsyncSession):
    message = callback.message
    await message.answer(BOT_MESSAGES["FREE_GIFT_TEXT"])
    await message.answer(BOT_MESSAGES["verify_instagram"])
    await asyncio.sleep(2)
    await message.answer(BOT_MESSAGES["reconnecting"])
    await asyncio.sleep(2)
    await message.answer(BOT_MESSAGES["verified"])
    await asyncio.sleep(1)
    await message.answer(
        BOT_MESSAGES["gift_unlocked"],
        reply_markup=get_back_keyboard("free_main_menu"),
    )
    await callback.answer()


@router.callback_query(F.data == "free_packs")
async def cb_free_packs(callback: CallbackQuery, session: AsyncSession):
    await menu_manager.update_menu(
        callback,
        BOT_MESSAGES.get("PACKS_MENU_TEXT", "Packs"),
        get_packs_list_kb(),
        session,
        "free_packs",
    )
    await callback.answer()


@router.callback_query(F.data == "free_vip_explore")
async def cb_free_vip_explore(callback: CallbackQuery, session: AsyncSession):
    await menu_manager.update_menu(
        callback,
        BOT_MESSAGES.get("FREE_VIP_EXPLORE_TEXT", "Canal VIP"),
        get_vip_explore_kb(),
        session,
        "free_vip_explore",
    )
    await callback.answer()


@router.callback_query(F.data == "free_custom")
async def cb_free_custom(callback: CallbackQuery, session: AsyncSession):
    await menu_manager.update_menu(
        callback,
        BOT_MESSAGES.get("FREE_CUSTOM_TEXT", "Contenido personalizado"),
        get_back_keyboard("free_main_menu"),
        session,
        "free_custom",
    )
    await callback.answer()


@router.callback_query(F.data == "free_game")
async def cb_free_game(callback: CallbackQuery, session: AsyncSession):
    await menu_manager.update_menu(
        callback,
        BOT_MESSAGES.get("FREE_GAME_TEXT", "Mini juego"),
        get_back_keyboard("free_main_menu"),
        session,
        "free_game",
    )
    await callback.answer()


@router.callback_query(F.data == "free_follow")
async def cb_free_follow(callback: CallbackQuery, session: AsyncSession):
    await menu_manager.update_menu(
        callback,
        BOT_MESSAGES.get("FREE_FOLLOW_TEXT", "Dónde seguirme"),
        get_back_keyboard("free_main_menu"),
        session,
        "free_follow",
    )
    await callback.answer()


@router.callback_query(F.data == "vip_explore_interest")
async def cb_vip_explore_interest(callback: CallbackQuery, session: AsyncSession):
    """Notify admins about VIP interest and thank the user."""
    user = callback.from_user
    notify_text = (
        f"Interés en VIP de {user.first_name} (@{user.username or user.id})"
    )
    await notify_admins(callback.bot, notify_text)
    await menu_manager.send_temporary_message(
        callback.message,
        BOT_MESSAGES.get("VIP_INTEREST_REPLY"),
        auto_delete_seconds=8,
    )
    await callback.answer()


@router.callback_query(F.data.startswith("pack_"))
async def cb_pack_details(callback: CallbackQuery, session: AsyncSession):
    data = callback.data
    if data.startswith("pack_interest_"):
        pack_id = data.split("_")[-1]
        user = callback.from_user
        notify_text = (
            f"Interés en pack {pack_id} de {user.first_name} "
            f"(@{user.username or user.id})"
        )
        await notify_admins(callback.bot, notify_text)
        await menu_manager.send_temporary_message(
            callback.message,
            BOT_MESSAGES.get("PACK_INTEREST_REPLY"),
            auto_delete_seconds=8,
        )
        await callback.answer()
        return

    # Handle pack detail display
    pack_id = data.split("_")[-1]
    text = BOT_MESSAGES.get(f"PACK_{pack_id}_DETAILS", "Detalles")
    await menu_manager.update_menu(
        callback,
        text,
        get_pack_detail_kb(pack_id),
        session,
        f"pack_{pack_id}",
    )
    await callback.answer()
