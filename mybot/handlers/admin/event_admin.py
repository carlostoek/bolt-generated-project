from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from utils.user_roles import is_admin
from utils.menu_utils import update_menu
from keyboards.admin_event_kb import (
    get_admin_event_main_kb,
    get_event_menu_kb,
    get_raffle_menu_kb,
)
from keyboards.common import get_back_kb
from utils.admin_state import AdminEventStates, AdminRaffleStates
from services import EventService, RaffleService

router = Router()


@router.callback_query(F.data == "admin_manage_events_sorteos")
async def admin_events_main(callback: CallbackQuery, session: AsyncSession):
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer()
    await update_menu(
        callback,
        "Gestionar Eventos y Sorteos",
        get_admin_event_main_kb(),
        session,
        "admin_manage_events_sorteos",
    )
    await callback.answer()


@router.callback_query(F.data == "event_menu")
async def event_menu(callback: CallbackQuery, session: AsyncSession):
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer()
    await update_menu(
        callback,
        "Menú de Eventos",
        get_event_menu_kb(),
        session,
        "event_menu",
    )
    await callback.answer()


@router.callback_query(F.data == "raffle_menu")
async def raffle_menu(callback: CallbackQuery, session: AsyncSession):
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer()
    await update_menu(
        callback,
        "Menú de Sorteos",
        get_raffle_menu_kb(),
        session,
        "raffle_menu",
    )
    await callback.answer()


# ----- Event creation flow -----

@router.callback_query(F.data == "create_event")
async def start_create_event(callback: CallbackQuery, state: FSMContext):
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer()
    await callback.message.edit_text(
        "Nombre del evento:", reply_markup=get_back_kb("event_menu")
    )
    await state.set_state(AdminEventStates.creating_event_name)
    await callback.answer()


@router.message(AdminEventStates.creating_event_name)
async def process_event_name(message: Message, state: FSMContext):
    if not await is_admin(message.from_user.id, session):
        return
    await state.update_data(name=message.text)
    await message.answer("Descripción del evento:")
    await state.set_state(AdminEventStates.creating_event_description)


@router.message(AdminEventStates.creating_event_description)
async def process_event_description(message: Message, state: FSMContext):
    if not await is_admin(message.from_user.id, session):
        return
    await state.update_data(description=message.text)
    await message.answer("Multiplicador de puntos (ej. 2 para doble):")
    await state.set_state(AdminEventStates.creating_event_multiplier)


@router.message(AdminEventStates.creating_event_multiplier)
async def finish_event_create(message: Message, state: FSMContext, session: AsyncSession):
    if not await is_admin(message.from_user.id, session):
        return
    try:
        multiplier = int(message.text)
    except ValueError:
        await message.answer("Ingresa un número válido:")
        return
    data = await state.get_data()
    service = EventService(session)
    await service.create_event(data["name"], data["description"], multiplier)
    await message.answer(
        "Evento creado.", reply_markup=get_event_menu_kb()
    )
    await state.clear()


# ----- List events -----

@router.callback_query(F.data == "list_events")
async def list_events(callback: CallbackQuery, session: AsyncSession):
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer()
    service = EventService(session)
    events = await service.list_active_events()
    if events:
        lines = [f"{e.id}. {e.name} x{e.multiplier}" for e in events]
        text = "Eventos activos:\n" + "\n".join(lines)
    else:
        text = "No hay eventos activos."
    await callback.message.edit_text(text, reply_markup=get_back_kb("event_menu"))
    await callback.answer()


# ----- End event -----

@router.callback_query(F.data == "end_event")
async def choose_event_end(callback: CallbackQuery, session: AsyncSession):
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer()
    service = EventService(session)
    events = await service.list_active_events()
    if not events:
        await callback.answer("No hay eventos activos", show_alert=True)
        return
    from aiogram.utils.keyboard import InlineKeyboardBuilder

    builder = InlineKeyboardBuilder()
    for ev in events:
        builder.button(text=ev.name, callback_data=f"end_event_{ev.id}")
    builder.button(text="🔙 Volver", callback_data="event_menu")
    builder.adjust(1)
    await callback.message.edit_text(
        "Selecciona el evento a finalizar:", reply_markup=builder.as_markup()
    )
    await callback.answer()


@router.callback_query(F.data.startswith("end_event_"))
async def finish_event(callback: CallbackQuery, session: AsyncSession):
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer()
    event_id = int(callback.data.split("_")[-1])
    service = EventService(session)
    await service.end_event(event_id)
    await callback.message.edit_text(
        "Evento finalizado.", reply_markup=get_event_menu_kb()
    )
    await callback.answer()


# ----- Raffle creation flow -----

@router.callback_query(F.data == "create_raffle")
async def start_create_raffle(callback: CallbackQuery, state: FSMContext):
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer()
    await callback.message.edit_text(
        "Nombre del sorteo:", reply_markup=get_back_kb("raffle_menu")
    )
    await state.set_state(AdminRaffleStates.creating_raffle_name)
    await callback.answer()


@router.message(AdminRaffleStates.creating_raffle_name)
async def raffle_name(message: Message, state: FSMContext):
    if not await is_admin(message.from_user.id, session):
        return
    await state.update_data(name=message.text)
    await message.answer("Descripción del sorteo:")
    await state.set_state(AdminRaffleStates.creating_raffle_description)


@router.message(AdminRaffleStates.creating_raffle_description)
async def raffle_desc(message: Message, state: FSMContext):
    if not await is_admin(message.from_user.id, session):
        return
    await state.update_data(description=message.text)
    await message.answer("Premio del sorteo:")
    await state.set_state(AdminRaffleStates.creating_raffle_prize)


@router.message(AdminRaffleStates.creating_raffle_prize)
async def raffle_finish(message: Message, state: FSMContext, session: AsyncSession):
    if not await is_admin(message.from_user.id, session):
        return
    data = await state.get_data()
    service = RaffleService(session)
    await service.create_raffle(data["name"], data["description"], message.text)
    await message.answer(
        "Sorteo creado.", reply_markup=get_raffle_menu_kb()
    )
    await state.clear()


# ----- List raffles -----

@router.callback_query(F.data == "list_raffles")
async def list_raffles(callback: CallbackQuery, session: AsyncSession):
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer()
    service = RaffleService(session)
    raffles = await service.list_active_raffles()
    if raffles:
        lines = [f"{r.id}. {r.name} - premio {r.prize}" for r in raffles]
        text = "Sorteos activos:\n" + "\n".join(lines)
    else:
        text = "No hay sorteos activos."
    await callback.message.edit_text(text, reply_markup=get_back_kb("raffle_menu"))
    await callback.answer()


# ----- End raffle -----

@router.callback_query(F.data == "end_raffle")
async def choose_raffle_end(callback: CallbackQuery, session: AsyncSession):
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer()
    service = RaffleService(session)
    raffles = await service.list_active_raffles()
    if not raffles:
        await callback.answer("No hay sorteos activos", show_alert=True)
        return
    from aiogram.utils.keyboard import InlineKeyboardBuilder

    builder = InlineKeyboardBuilder()
    for r in raffles:
        builder.button(text=r.name, callback_data=f"end_raffle_{r.id}")
    builder.button(text="🔙 Volver", callback_data="raffle_menu")
    builder.adjust(1)
    await callback.message.edit_text(
        "Selecciona el sorteo a finalizar:", reply_markup=builder.as_markup()
    )
    await callback.answer()


@router.callback_query(F.data.startswith("end_raffle_"))
async def finish_raffle(callback: CallbackQuery, session: AsyncSession):
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer()
    raffle_id = int(callback.data.split("_")[-1])
    service = RaffleService(session)
    raffle = await service.end_raffle(raffle_id)
    if raffle and raffle.winner_id:
        msg = f"Sorteo finalizado. Ganador ID {raffle.winner_id}"
    else:
        msg = "Sorteo finalizado. Sin participantes."
    await callback.message.edit_text(msg, reply_markup=get_raffle_menu_kb())
    await callback.answer()
