from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from sqlalchemy.ext.asyncio import AsyncSession

from utils.user_roles import is_admin
from utils.menu_utils import update_menu, send_temporary_reply
from keyboards.admin_channels_kb import get_admin_channels_kb, get_wait_time_kb
from keyboards.common import get_back_kb
from services.channel_service import ChannelService
from services.config_service import ConfigService
from database.models import BotConfig

router = Router()


class ChannelStates(StatesGroup):
    waiting_for_vip_channel_id = State()
    waiting_for_free_channel_id = State()


@router.callback_query(F.data == "admin_channels")
async def channels_menu(callback: CallbackQuery, session: AsyncSession):
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer()
    service = ChannelService(session)
    channels = await service.list_channels()
    if channels:
        lines = [f"- {c.title or c.id} (<code>{c.id}</code>)" for c in channels]
        text = "Administrar canales\n\n" + "\n".join(lines)
    else:
        text = "Administrar canales\n\nNo hay canales configurados."
    await update_menu(
        callback,
        text,
        get_admin_channels_kb(channels),
        session,
        "admin_channels",
    )
    await callback.answer()


@router.callback_query(F.data == "admin_add_channel")
async def prompt_add_channel(callback: CallbackQuery, state: FSMContext):
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer()
    await callback.message.edit_text(
        "Ingresa el ID del canal VIP o reenv\u00eda un mensaje del canal aqu\u00ed.\n"
        "Puedes escribir directamente el ID del canal (debes ser administrador del canal para obtenerlo), "
        "o puedes reenviar un mensaje del canal aqu\u00ed y el bot extraer\u00e1 autom\u00e1ticamente el ID del remitente.",
        reply_markup=get_back_kb("admin_channels"),
    )
    await state.set_state(ChannelStates.waiting_for_vip_channel_id)
    await callback.answer()


@router.message(ChannelStates.waiting_for_vip_channel_id)
async def receive_vip_channel(message: Message, state: FSMContext, session: AsyncSession):
    if not await is_admin(message.from_user.id, session):
        return
    chat_id = None
    if message.forward_from_chat:
        chat_id = message.forward_from_chat.id
    else:
        try:
            chat_id = int(message.text.strip())
        except (TypeError, ValueError):
            await send_temporary_reply(message, "ID inválido. Intenta de nuevo.")
            return
    await state.update_data(vip_channel_id=chat_id)
    await message.answer(
        "Ahora ingresa el ID del canal FREE o reenv\u00eda un mensaje del canal.",
        reply_markup=get_back_kb("admin_channels"),
    )
    await state.set_state(ChannelStates.waiting_for_free_channel_id)


@router.message(ChannelStates.waiting_for_free_channel_id)
async def receive_free_channel(message: Message, state: FSMContext, session: AsyncSession):
    if not await is_admin(message.from_user.id, session):
        return
    chat_id = None
    if message.forward_from_chat:
        chat_id = message.forward_from_chat.id
    else:
        try:
            chat_id = int(message.text.strip())
        except (TypeError, ValueError):
            await send_temporary_reply(message, "ID inválido. Intenta de nuevo.")
            return
    data = await state.get_data()
    vip_id = int(data.get("vip_channel_id"))
    config = ConfigService(session)
    await config.set_vip_channel_id(vip_id)
    await config.set_free_channel_id(chat_id)

    channel_service = ChannelService(session)
    await channel_service.add_channel(vip_id)
    await channel_service.add_channel(chat_id)

    await message.answer(
        f"Canales registrados correctamente. Canal VIP: {vip_id}, Canal FREE: {chat_id}",
        reply_markup=get_admin_channels_kb(await channel_service.list_channels()),
    )
    await state.clear()


@router.callback_query(F.data == "admin_wait_time")
async def wait_time_menu(callback: CallbackQuery, session: AsyncSession):
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer()
    config = await session.get(BotConfig, 1)
    current = config.free_channel_wait_time_minutes if config else 0
    await update_menu(
        callback,
        f"Tiempo actual: {current} minutos",
        get_wait_time_kb(),
        session,
        "admin_wait_time",
    )
    await callback.answer()


@router.callback_query(F.data.startswith("wait_"))
async def set_wait_time(callback: CallbackQuery, session: AsyncSession):
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer()
    minutes = int(callback.data.split("_")[1])
    config = await session.get(BotConfig, 1)
    if not config:
        config = BotConfig(id=1)
        session.add(config)
    config.free_channel_wait_time_minutes = minutes
    await session.commit()
    service = ChannelService(session)
    channels = await service.list_channels()
    if channels:
        lines = [f"- {c.title or c.id} (<code>{c.id}</code>)" for c in channels]
        text = f"Tiempo actualizado a {minutes} minutos.\n\n" + "\n".join(lines)
    else:
        text = f"Tiempo actualizado a {minutes} minutos."
    await update_menu(
        callback,
        text,
        get_admin_channels_kb(channels),
        session,
        "admin_channels",
    )
    await callback.answer()


@router.callback_query(F.data.startswith("remove_channel_"))
async def remove_channel(callback: CallbackQuery, session: AsyncSession):
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer()
    chat_id = int(callback.data.split("_")[-1])
    service = ChannelService(session)
    await service.remove_channel(chat_id)
    channels = await service.list_channels()
    if channels:
        lines = [f"- {c.title or c.id} (<code>{c.id}</code>)" for c in channels]
        text = "Canales actualizados:\n\n" + "\n".join(lines)
    else:
        text = "No hay canales configurados."
    await update_menu(
        callback,
        text,
        get_admin_channels_kb(channels),
        session,
        "admin_channels",
    )
    await callback.answer("Canal eliminado")
