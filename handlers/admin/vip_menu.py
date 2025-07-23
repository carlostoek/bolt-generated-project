from aiogram import Router, F, Bot
from aiogram.types import CallbackQuery, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardButton
from aiogram import Router, F, Bot
from aiogram.types import CallbackQuery, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardButton
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime

from utils.user_roles import is_admin, is_vip_member
from keyboards.admin_vip_kb import get_admin_vip_kb
from keyboards.admin_vip_config_kb import (
    get_admin_vip_config_kb,
    get_tariff_select_kb,
    get_vip_messages_kb,
)
from keyboards.admin_vip_channel_kb import get_admin_vip_channel_kb
from utils.keyboard_utils import (
    get_back_keyboard,
    get_main_menu_keyboard,
    get_post_confirmation_keyboard,
)
from services import (
    SubscriptionService,
    ConfigService,
    TokenService,
    get_admin_statistics,
    BadgeService,
    AchievementService,
    MissionService,
)
from database.models import User, Tariff
from utils.message_utils import get_profile_message
from utils.text_utils import sanitize_text
from utils.admin_state import (
    AdminVipMessageStates,
    AdminManualBadgeStates,
    AdminContentStates,
    AdminVipSubscriberStates,
)
from aiogram.fsm.context import FSMContext
from utils.menu_utils import (
    update_menu,
    send_temporary_reply,
    send_clean_message,
)
from services.message_service import MessageService
from database.models import set_user_menu_state
import logging


logger = logging.getLogger(__name__)
router = Router()


@router.callback_query(F.data == "vip_none")
async def vip_none(callback: CallbackQuery):
    await callback.answer()


@router.callback_query(F.data == "admin_vip")
async def vip_menu(callback: CallbackQuery, session: AsyncSession):
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer()
    await update_menu(
        callback,
        "🔐 Administración Canal VIP",
        get_admin_vip_channel_kb(),
        session,
        "admin_vip",
    )
    await callback.answer()


@router.callback_query(F.data == "vip_generate_token")
async def vip_generate_token(callback: CallbackQuery, session: AsyncSession):
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer()
    
    # Get available tariffs
    result = await session.execute(select(Tariff))
    tariffs = result.scalars().all()
    
    if not tariffs:
        await callback.answer("❌ No hay tarifas configuradas. Configura las tarifas primero.", show_alert=True)
        return
    
    builder = InlineKeyboardBuilder()
    for t in tariffs:
        builder.button(text=f"{t.name} ({t.duration_days}d - ${t.price})", callback_data=f"vip_token_{t.id}")
    builder.button(text="🔙 Volver", callback_data="admin_vip")
    builder.adjust(1)
    
    await update_menu(
        callback,
        "💳 Selecciona la tarifa para generar token:",
        builder.as_markup(),
        session,
        "admin_vip_generate_token",
    )
    await callback.answer()


@router.callback_query(F.data.startswith("vip_token_"))
async def vip_create_token(callback: CallbackQuery, session: AsyncSession, bot: Bot):
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer()
    
    tariff_id = int(callback.data.split("_")[-1])
    tariff = await session.get(Tariff, tariff_id)
    
    if not tariff:
        await callback.answer("❌ Tarifa no encontrada", show_alert=True)
        return
    
    service = TokenService(session)
    token = await service.create_vip_token(tariff_id)
    
    # Get bot username for the link
    bot_username = (await bot.get_me()).username
    link = f"https://t.me/{bot_username}?start={token.token_string}"
    
    builder = InlineKeyboardBuilder()
    builder.button(text="❌ Invalidar Token", callback_data=f"vip_invalidate_{token.token_string}"),
    builder.button(text="🔄 Generar Otro"),
    builder.button(text="🔙 Volver", callback_data="admin_vip"),
    builder.adjust(1)
    
    message_text = (
        f"✅ **Token VIP Generado**\n\n"
        f"📋 **Tarifa:** {tariff.name}\n"
        f"⏱️ **Duración:** {tariff.duration_days} días\n"
        f"💰 **Precio:** ${tariff.price}\n\n"
        f"🔗 **Enlace de activación:**\n`{link}`\n\n"
        f"⚠️ Comparte este enlace con el cliente. Una vez usado, no se puede reutilizar."
    )
    
    await callback.message.edit_text(message_text, reply_markup=builder.as_markup(), parse_mode="Markdown")
    logger.info(f"Admin {callback.from_user.id} generated VIP token for tariff {tariff.name}")
    await callback.answer()


@router.callback_query(F.data.startswith("vip_invalidate_"))
async def vip_invalidate_token(callback: CallbackQuery, session: AsyncSession):
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer()
    
    token_string = callback.data.split("_", 2)[-1]  # Get everything after "vip_invalidate_"
    service = TokenService(session)
    
    success = await service.invalidate_vip_token(token_string)
    
    if success:
        await callback.answer("✅ Token invalidado correctamente", show_alert=True)
        logger.info(f"Admin {callback.from_user.id} invalidated token {token_string}")
        # Return to VIP menu
        await update_menu(
            callback,
            "🔐 Administración Canal VIP",
            get_admin_vip_kb(),
            session,
            "admin_vip",
        )
    else:
        await callback.answer("❌ Token no encontrado o ya usado", show_alert=True)


@router.callback_query(F.data == "vip_stats")
async def vip_stats(callback: CallbackQuery, session: AsyncSession):
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer()
    
    stats = await get_admin_statistics(session)
    
    # Get token statistics
    stmt = select(Tariff)
    result = await session.execute(stmt)
    tariffs = result.scalars().all()
    
    text_lines = [
        "📊 **Estadísticas VIP**",
        "",
        f"👥 **Usuarios totales:** {stats['users_total']}",
        f"💎 **Suscripciones totales:** {stats['subscriptions_total']}",
        f"✅ **Activas:** {stats['subscriptions_active']}",
        f"❌ **Expiradas:** {stats['subscriptions_expired']}",
        f"💰 **Ingresos totales:** ${stats.get('revenue_total', 0)}",
        "",
        "📋 **Tarifas disponibles:**"
    ]
    
    if tariffs:
        for t in tariffs:
            text_lines.append(f"• {t.name}: {t.duration_days}d - ${t.price}")
    else:
        text_lines.append("• No hay tarifas configuradas")

    builder = InlineKeyboardBuilder()
    builder.button(text="🔙 Volver", callback_data="admin_vip")
    builder.adjust(1)
    
    await callback.message.edit_text(
        "\n".join(text_lines), 
        reply_markup=builder.as_markup(), 
        parse_mode="Markdown"
    )
    await set_user_menu_state(session, callback.from_user.id, "admin_vip_stats")
    await callback.answer()


@router.callback_query(F.data == "vip_manual_badge")
async def vip_manual_badge(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer()
    await callback.message.edit_text(
        "👤 Ingresa el ID o username del usuario:",
        reply_markup=get_back_keyboard("admin_vip"),
    )
    await state.set_state(AdminManualBadgeStates.waiting_for_user)
    await callback.answer()


@router.message(AdminManualBadgeStates.waiting_for_user, F.text)
async def process_manual_badge_user(message: Message, state: FSMContext, session: AsyncSession):
    if not await is_admin(message.from_user.id, session):
        return
    query = message.text.strip()
    user = None
    if query.isdigit():
        user = await session.get(User, int(query))
    else:
        username = query.lstrip("@")
        stmt = select(User).where(User.username.ilike(username))
        result = await session.execute(stmt)
        user = result.scalar_one_or_none()
    if not user:
        await send_temporary_reply(message, "❌ Usuario no encontrado. Intenta nuevamente:")
        return
    await state.update_data(target_user=user.id)
    badges = await BadgeService(session).list_badges()
    if not badges:
        await send_temporary_reply(
            message,
            "❌ No hay insignias disponibles.",
            reply_markup=get_back_keyboard("admin_vip"),
        )
        await state.clear()
        return
    builder = InlineKeyboardBuilder()
    for b in badges:
        label = f"{b.emoji or ''} {b.name}".strip()
        builder.button(text=label, callback_data=f"manual_badge_{b.id}")
    builder.button(text="🔙 Volver", callback_data="admin_vip")
    builder.adjust(1)
    await message.answer("🏅 Selecciona la insignia a otorgar:", reply_markup=builder.as_markup())
    await state.set_state(AdminManualBadgeStates.waiting_for_badge)


@router.callback_query(F.data.startswith("manual_badge_"))
async def assign_manual_badge(callback: CallbackQuery, state: FSMContext, session: AsyncSession, bot: Bot):
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer()
    data = await state.get_data()
    user_id = data.get("target_user")
    if not user_id:
        await callback.answer("❌ Usuario no especificado", show_alert=True)
        return
    badge_id = int(callback.data.split("_")[-1])
    ach_service = AchievementService(session)
    success = await ach_service.award_badge(user_id, badge_id, force=True)
    if success:
        await callback.answer("✅ Insignia otorgada", show_alert=True)
        try:
            await bot.send_message(user_id, "🏅 ¡Has recibido una nueva insignia!")
        except Exception:
            pass
    else:
        await callback.answer("❌ No se pudo otorgar la insignia", show_alert=True)
    await state.clear()
    await update_menu(callback, "🔐 Administración Canal VIP", get_admin_vip_kb(), session, "admin_vip")


@router.callback_query(F.data == "admin_send_channel_post")
async def vip_send_channel_post(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer()
    await send_clean_message(
        callback.message,
        "📝 Envía el texto que deseas publicar en el canal VIP:",
        reply_markup=get_back_keyboard("admin_vip"),
    )
    await state.set_state(AdminContentStates.waiting_for_channel_post_text)
    await callback.answer()


@router.message(AdminContentStates.waiting_for_channel_post_text)
async def process_vip_channel_post(message: Message, state: FSMContext, session: AsyncSession, bot: Bot):
    if not await is_admin(message.from_user.id, session):
        return
    await state.update_data(post_text=message.text)
    await send_clean_message(
        message,
        f"📋 **Previsualización:**\n{message.text}\n\n¿Deseas publicarlo en el canal VIP?",
        reply_markup=get_post_confirmation_keyboard(),
    )
    await state.set_state(AdminContentStates.confirming_channel_post)


@router.callback_query(AdminContentStates.confirming_channel_post, F.data == "confirm_channel_post")
async def confirm_vip_channel_post(callback: CallbackQuery, state: FSMContext, session: AsyncSession, bot: Bot):
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer()
    data = await state.get_data()
    text = data.get("post_text")
    service = MessageService(session, bot)
    sent = await service.send_interactive_post(text, "vip")
    if sent is None:
        reply = "❌ Canal VIP no configurado."
    elif sent is False:
        reply = "❌ No se pudo publicar en el canal. Revisa los permisos del bot."
    else:
        reply = f"✅ Mensaje publicado con ID {sent.message_id}"
    await callback.message.edit_text(reply, reply_markup=get_admin_vip_kb())
    await state.clear()
    await callback.answer()


@router.callback_query(AdminContentStates.confirming_channel_post, F.data == "admin_vip")
async def cancel_vip_channel_post(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer()
    await state.clear()
    await update_menu(
        callback,
        "🔐 Administración Canal VIP",
        get_admin_vip_kb(),
        session,
        "admin_vip",
    )
    await callback.answer()


@router.callback_query(F.data.startswith("vip_manage"))
async def manage_subs(callback: CallbackQuery, session: AsyncSession):
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer()
    parts = callback.data.split(":")
    page = int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else 0
    sub_service = SubscriptionService(session)
    subs = await sub_service.get_active_subscribers()
    page_size = 10
    start = page * page_size
    current = subs[start : start + page_size]

    builder = InlineKeyboardBuilder()
    for sub in current:
        user = await session.get(User, sub.user_id)
        username = sanitize_text(user.username) if user else None
        display = username or (user.first_name or "Sin nombre") if user else str(sub.user_id)
        builder.row(InlineKeyboardButton(text=display, callback_data="vip_none"))
        builder.row(
            InlineKeyboardButton(text="👤", callback_data=f"vip_profile_{sub.user_id}"),
            InlineKeyboardButton(text="➕", callback_data=f"vip_add_{sub.user_id}"),
            InlineKeyboardButton(text="🚫", callback_data=f"vip_kick_{sub.user_id}"),
            InlineKeyboardButton(text="✏️", callback_data=f"vip_edit_{sub.user_id}"),
        )

    if start > 0 or start + page_size < len(subs):
        nav = []
        if start > 0:
            nav.append(InlineKeyboardButton(text="⬅️", callback_data=f"vip_manage:{page - 1}"))
        if start + page_size < len(subs):
            nav.append(InlineKeyboardButton(text="➡️", callback_data=f"vip_manage:{page + 1}"))
        builder.row(*nav)
    builder.row(InlineKeyboardButton(text="🔙 Volver", callback_data="admin_vip"))

    await update_menu(
        callback,
        "👥 Suscriptores VIP activos:",
        builder.as_markup(),
        session,
        "admin_vip_manage",
    )
    await callback.answer()


@router.callback_query(F.data.startswith("vip_add_"))
async def vip_add_days(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer()
    user_id = int(callback.data.split("_")[-1])
    await state.update_data(target_user=user_id)
    await callback.message.answer(
        "Ingresa la cantidad de días a agregar:",
        reply_markup=get_back_keyboard("vip_manage"),
    )
    await state.set_state(AdminVipSubscriberStates.waiting_for_days)
    await callback.answer()


@router.callback_query(F.data.startswith("vip_kick_"))
async def vip_kick(callback: CallbackQuery, session: AsyncSession):
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer()
    user_id = int(callback.data.split("_")[-1])
    sub_service = SubscriptionService(session)
    await sub_service.revoke_subscription(user_id, bot=callback.bot)
    await callback.answer("❌ Suscriptor expulsado", show_alert=True)


@router.callback_query(F.data.startswith("vip_profile_"))
async def vip_profile(callback: CallbackQuery, session: AsyncSession):
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer()
    user_id = int(callback.data.split("_")[-1])
    user = await session.get(User, user_id)
    if not user:
        return await callback.answer("Usuario no encontrado", show_alert=True)
    mission_service = MissionService(session)
    missions = await mission_service.get_active_missions(user_id=user_id)
    profile_text = await get_profile_message(user, missions, session)
    sub_service = SubscriptionService(session)
    sub = await sub_service.get_subscription(user_id)
    if sub and sub.expires_at:
        profile_text += f"\n\nVIP hasta: {sub.expires_at.strftime('%d/%m/%Y')}"
    await callback.message.answer(profile_text)
    await callback.answer()


@router.callback_query(F.data.startswith("vip_edit_"))
async def vip_edit(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer()
    user_id = int(callback.data.split("_")[-1])
    await state.update_data(target_user=user_id)
    await callback.message.answer(
        "Ingresa la nueva fecha de expiración (DD/MM/AAAA) o 0 para ilimitado:",
        reply_markup=get_back_keyboard("vip_manage"),
    )
    await state.set_state(AdminVipSubscriberStates.waiting_for_new_date)
    await callback.answer()


@router.message(AdminVipSubscriberStates.waiting_for_days)
async def process_add_days(message: Message, state: FSMContext, session: AsyncSession):
    if not await is_admin(message.from_user.id, session):
        return
    try:
        days = int(message.text)
    except ValueError:
        await send_temporary_reply(message, "Ingresa un número válido de días.")
        return
    data = await state.get_data()
    user_id = data.get("target_user")
    sub_service = SubscriptionService(session)
    await sub_service.extend_subscription(user_id, days)
    await message.answer(f"✅ Suscripción extendida {days} días")
    await state.clear()


@router.message(AdminVipSubscriberStates.waiting_for_new_date)
async def process_edit_date(message: Message, state: FSMContext, session: AsyncSession):
    if not await is_admin(message.from_user.id, session):
        return
    text = message.text.strip()
    from datetime import datetime
    if text == "0":
        new_date = None
    else:
        try:
            new_date = datetime.strptime(text, "%d/%m/%Y")
        except ValueError:
            await send_temporary_reply(message, "Formato inválido. Usa DD/MM/AAAA o 0.")
            return
    data = await state.get_data()
    user_id = data.get("target_user")
    sub_service = SubscriptionService(session)
    await sub_service.set_subscription_expiration(user_id, new_date)
    await message.answer("✅ Fecha de expiración actualizada")
    await state.clear()


@router.callback_query(F.data == "vip_config")
async def vip_config(callback: CallbackQuery, session: AsyncSession):
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer()
    config = ConfigService(session)
    price = await config.get_value("vip_price")
    price_text = price or "No establecido"
    await update_menu(
        callback,
        f"⚙️ **Configuración VIP**\n\nPrecio actual: {price_text}",
        get_admin_vip_config_kb(),
        session,
        "vip_config",
    )
    await callback.answer()


@router.callback_query(F.data == "vip_config_messages")
async def vip_config_messages(callback: CallbackQuery, session: AsyncSession):
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer()
    await update_menu(
        callback,
        "💬 Configura los mensajes del canal VIP",
        get_vip_messages_kb(),
        session,
        "vip_message_config",
    )
    await callback.answer()


@router.callback_query(F.data == "edit_vip_reminder")
async def prompt_vip_reminder(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer()
    config = ConfigService(session)
    current = await config.get_value("vip_reminder_message") or "Tu suscripción VIP expira pronto."
    await callback.message.edit_text(
        f"📝 **Mensaje de recordatorio actual:**\n{current}\n\nEnvía el nuevo mensaje:",
        reply_markup=get_back_keyboard("vip_config_messages"),
    )
    await state.set_state(AdminVipMessageStates.waiting_for_reminder_message)
    await callback.answer()


@router.message(AdminVipMessageStates.waiting_for_reminder_message)
async def set_vip_reminder(message: Message, state: FSMContext, session: AsyncSession):
    if not await is_admin(message.from_user.id, session):
        return
    
    new_message = message.text.strip()
    await ConfigService(session).set_value("vip_reminder_message", new_message)
    
    await message.answer(
        "✅ Mensaje de recordatorio actualizado",
        reply_markup=get_vip_messages_kb()
    )
    await state.clear()


@router.callback_query(F.data == "edit_vip_welcome")
async def prompt_vip_welcome(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer()
    
    config = ConfigService(session)
    current = await config.get_value("vip_welcome_message") or "¡Bienvenido al canal VIP!"
    
    await callback.message.edit_text(
        f"📝 **Mensaje de bienvenida actual:**\n{current}\n\nEnvía el nuevo mensaje:",
        reply_markup=get_back_keyboard("vip_config_messages")
    )
    await state.set_state(AdminVipMessageStates.waiting_for_welcome_message)
    await callback.answer()


@router.message(AdminVipMessageStates.waiting_for_welcome_message)
async def set_vip_welcome(message: Message, state: FSMContext, session: AsyncSession):
    if not await is_admin(message.from_user.id, session):
        return
    
    new_message = message.text.strip()
    await ConfigService(session).set_value("vip_welcome_message", new_message)
    
    await message.answer(
        "✅ Mensaje de bienvenida actualizado",
        reply_markup=get_vip_messages_kb()
    )
    await state.clear()


@router.callback_query(F.data == "edit_vip_expired")
async def prompt_vip_expired(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer()
    
    config = ConfigService(session)
    current = await config.get_value("vip_expired_message") or "Tu suscripción VIP ha expirado."
    
    await callback.message.edit_text(
        f"📝 **Mensaje de expiración actual:**\n{current}\n\nEnvía el nuevo mensaje:",
        reply_markup=get_back_keyboard("vip_config_messages")
    )
    await state.set_state(AdminVipMessageStates.waiting_for_expired_message)
    await callback.answer()


@router.message(AdminVipMessageStates.waiting_for_expired_message)
async def set_vip_expired(message: Message, state: FSMContext, session: AsyncSession):
    if not await is_admin(message.from_user.id, session):
        return
    
    new_message = message.text.strip()
    await ConfigService(session).set_value("vip_expired_message", new_message)
    
    await message.answer(
        "✅ Mensaje de expiración actualizado",
        reply_markup=get_vip_messages_kb()
    )
    await state.clear()
