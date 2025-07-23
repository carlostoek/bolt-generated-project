from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from utils.user_roles import is_admin
from utils.admin_state import AdminTariffStates
from keyboards.tarifas_kb import (
    get_duration_kb,
    get_tarifas_kb,
    get_tariff_options_kb,
)
from keyboards.common import get_back_kb
from utils.menu_utils import send_temporary_reply, update_menu
from database.models import Tariff
from utils.text_utils import sanitize_text
import logging

logger = logging.getLogger(__name__)
router = Router()


@router.callback_query(F.data == "config_tarifas")
async def config_tarifas(callback: CallbackQuery, session: AsyncSession):
    """Show existing tariffs and menu options."""
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer()
    
    result = await session.execute(select(Tariff).order_by(Tariff.duration_days))
    tariffs = result.scalars().all()
    
    if tariffs:
        lines = [f"• **{t.name}**: {t.duration_days} días - ${t.price}" for t in tariffs]
        text = "💳 **Tarifas VIP configuradas:**\n\n" + "\n".join(lines)
    else:
        text = "💳 **Tarifas VIP**\n\nNo hay tarifas configuradas."
    
    await update_menu(callback, text, get_tarifas_kb(tariffs), session, "config_tarifas")
    await callback.answer()


@router.callback_query(F.data.startswith("tariff_"))
async def tariff_options(callback: CallbackQuery, session: AsyncSession):
    """Display options for a specific tariff."""
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer()

    if callback.data.startswith("edit_tariff_") or callback.data.startswith("delete_tariff_"):
        return
    tariff_id = int(callback.data.split("_")[-1])
    tariff = await session.get(Tariff, tariff_id)
    if not tariff:
        await callback.answer("❌ Tarifa no encontrada", show_alert=True)
        return

    text = (
        f"**{tariff.name}**\n"
        f"Duración: {tariff.duration_days} días\n"
        f"Precio: ${tariff.price}\n\n"
        "Elige una opción:"
    )
    await callback.message.edit_text(
        text,
        reply_markup=get_tariff_options_kb(tariff_id),
        parse_mode="Markdown",
    )
    await callback.answer()


@router.callback_query(F.data.startswith("edit_tariff_"))
async def start_edit_tariff(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    """Begin editing a tariff."""
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer()

    tariff_id = int(callback.data.split("edit_tariff_")[-1])
    tariff = await session.get(Tariff, tariff_id)
    if not tariff:
        await callback.answer("❌ Tarifa no encontrada", show_alert=True)
        return

    await state.update_data(tariff_id=tariff_id)
    await state.set_state(AdminTariffStates.editing_tariff_duration)
    await callback.message.edit_text(
        f"✏️ **Editar tarifa**\n\nDuración actual: {tariff.duration_days} días\n"
        f"Precio actual: ${tariff.price}\n\nSelecciona la nueva duración:",
        reply_markup=get_duration_kb(),
        parse_mode="Markdown",
    )
    await callback.answer()


@router.callback_query(AdminTariffStates.editing_tariff_duration)
async def edit_tariff_duration(callback: CallbackQuery, state: FSMContext):
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer()

    duration = int(callback.data.split("_")[-1])
    await state.update_data(duration_days=duration)
    await state.set_state(AdminTariffStates.editing_tariff_price)

    await callback.message.edit_text(
        f"💰 Ingresa el nuevo precio (solo números):",
    )
    await callback.answer()


@router.message(AdminTariffStates.editing_tariff_price)
async def edit_tariff_price(message: Message, state: FSMContext):
    if not await is_admin(message.from_user.id, session):
        return

    try:
        price = int(message.text.strip())
        if price <= 0:
            raise ValueError
    except ValueError:
        await send_temporary_reply(message, "❌ Precio inválido. Ingresa un número positivo.")
        return

    await state.update_data(price=price)
    await state.set_state(AdminTariffStates.editing_tariff_name)

    await message.answer("Ingresa el nuevo nombre de la tarifa:")


@router.message(AdminTariffStates.editing_tariff_name)
async def finish_edit_tariff(message: Message, state: FSMContext, session: AsyncSession):
    if not await is_admin(message.from_user.id, session):
        return

    name = sanitize_text(message.text.strip())
    if not name:
        await send_temporary_reply(message, "❌ El nombre no puede estar vacío.")
        return

    data = await state.get_data()
    tariff_id = data.get("tariff_id")
    tariff = await session.get(Tariff, tariff_id)
    if not tariff:
        await message.answer("❌ Tarifa no encontrada")
        await state.clear()
        return

    # Check if new name exists for a different tariff
    stmt = select(Tariff).where(Tariff.name.ilike(name), Tariff.id != tariff_id)
    result = await session.execute(stmt)
    existing = result.scalar_one_or_none()
    if existing:
        await send_temporary_reply(message, "❌ Ya existe una tarifa con ese nombre.")
        return

    tariff.duration_days = data.get("duration_days")
    tariff.price = data.get("price")
    tariff.name = name
    await session.commit()

    result = await session.execute(select(Tariff).order_by(Tariff.duration_days))
    tariffs = result.scalars().all()

    await message.answer(
        "✅ Tarifa actualizada",
        reply_markup=get_tarifas_kb(tariffs),
    )
    await state.clear()



@router.callback_query(F.data == "tarifa_new")
async def start_new_tarifa(callback: CallbackQuery, state: FSMContext):
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer()
    
    await state.set_state(AdminTariffStates.waiting_for_tariff_duration)
    await callback.message.edit_text(
        "⏱️ **Crear nueva tarifa**\n\nSelecciona la duración:", 
        reply_markup=get_duration_kb(),
        parse_mode="Markdown"
    )
    await callback.answer()


@router.message(Command("admin_configure_tariffs"))
async def admin_configure_tariffs(message: Message, state: FSMContext):
    if not await is_admin(message.from_user.id, session):
        return
    await state.set_state(AdminTariffStates.waiting_for_tariff_duration)
    await message.answer("⏱️ Selecciona la duración:", reply_markup=get_duration_kb())


@router.callback_query(AdminTariffStates.waiting_for_tariff_duration)
async def tariff_duration_selected(callback: CallbackQuery, state: FSMContext):
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer()
    
    duration = int(callback.data.split("_")[-1])
    await state.update_data(duration_days=duration)
    await state.set_state(AdminTariffStates.waiting_for_tariff_price)
    
    await callback.message.edit_text(
        f"💰 **Nueva tarifa - {duration} días**\n\nIngresa el precio (solo números):",
        parse_mode="Markdown"
    )
    await callback.answer()


@router.message(AdminTariffStates.waiting_for_tariff_price)
async def tariff_price(message: Message, state: FSMContext):
    if not await is_admin(message.from_user.id, session):
        return
    
    try:
        price = int(message.text.strip())
        if price <= 0:
            raise ValueError("Price must be positive")
    except ValueError:
        await send_temporary_reply(message, "❌ Precio inválido. Ingresa un número positivo.")
        return
    
    await state.update_data(price=price)
    await state.set_state(AdminTariffStates.waiting_for_tariff_name)
    
    data = await state.get_data()
    await message.answer(
        f"📝 **Nueva tarifa**\n"
        f"Duración: {data['duration_days']} días\n"
        f"Precio: ${price}\n\n"
        f"Ingresa el nombre de la tarifa:"
    )


@router.message(AdminTariffStates.waiting_for_tariff_name)
async def tariff_name(message: Message, state: FSMContext, session: AsyncSession):
    if not await is_admin(message.from_user.id, session):
        return
    
    name = sanitize_text(message.text.strip())
    if not name:
        await send_temporary_reply(message, "❌ El nombre no puede estar vacío.")
        return
    
    # Check if tariff name already exists
    stmt = select(Tariff).where(Tariff.name.ilike(name))
    result = await session.execute(stmt)
    existing = result.scalar_one_or_none()
    
    if existing:
        await send_temporary_reply(message, "❌ Ya existe una tarifa con ese nombre.")
        return
    
    data = await state.get_data()
    tariff = Tariff(
        name=name,
        duration_days=data["duration_days"],
        price=data["price"],
    )
    session.add(tariff)
    await session.commit()
    await session.refresh(tariff)
    
    success_msg = (
        f"✅ **Tarifa creada exitosamente**\n\n"
        f"📋 **Nombre:** {tariff.name}\n"
        f"⏱️ **Duración:** {tariff.duration_days} días\n"
        f"💰 **Precio:** ${tariff.price}"
    )
    
    await message.answer(success_msg, reply_markup=get_tarifas_kb(), parse_mode="Markdown")
    await state.clear()
    
    logger.info(f"Admin {message.from_user.id} created tariff: {tariff.name} ({tariff.duration_days}d, ${tariff.price})")


@router.callback_query(F.data.startswith("delete_tariff_"))
async def delete_tariff(callback: CallbackQuery, session: AsyncSession):
    """Delete a tariff (admin only)."""
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer()
    
    tariff_id = int(callback.data.split("_")[-1])
    tariff = await session.get(Tariff, tariff_id)
    
    if not tariff:
        await callback.answer("❌ Tarifa no encontrada", show_alert=True)
        return
    
    # Check if there are active tokens for this tariff
    from database.models import Token
    stmt = select(Token).where(Token.tariff_id == tariff_id, Token.is_used == False)
    result = await session.execute(stmt)
    active_tokens = result.scalars().all()
    
    if active_tokens:
        await callback.answer(
            f"❌ No se puede eliminar. Hay {len(active_tokens)} tokens activos para esta tarifa.", 
            show_alert=True
        )
        return
    
    await session.delete(tariff)
    await session.commit()
    
    await callback.answer("✅ Tarifa eliminada", show_alert=True)
    logger.info(f"Admin {callback.from_user.id} deleted tariff: {tariff.name}")
    
    # Refresh the tariffs list
    await config_tarifas(callback, session)
