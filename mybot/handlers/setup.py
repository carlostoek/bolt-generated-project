"""
Setup handlers for multi-tenant bot configuration.
Guides new admins through the initial setup process.
"""
import logging
from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy.ext.asyncio import AsyncSession

from utils.user_roles import is_admin
from utils.menu_manager import menu_manager
from services.tenant_service import TenantService
from keyboards.setup_kb import (
    get_setup_main_kb,
    get_setup_channels_kb,
    get_setup_gamification_kb,
    get_setup_tariffs_kb,
    get_setup_complete_kb,
    get_channel_detection_kb,
    get_setup_confirmation_kb
)
from utils.text_utils import sanitize_text

# Importar menu_factory para crear menús específicos si es necesario
from utils.menu_factory import menu_factory 

logger = logging.getLogger(__name__)
router = Router()

class SetupStates(StatesGroup):
    """States for the setup flow."""
    waiting_for_vip_channel = State()
    waiting_for_free_channel = State()
    waiting_for_channel_confirmation = State()
    waiting_for_manual_channel_id = State()
    # No necesitamos estados para configurar cada elemento si no hay interacción de FSM
    # directa más allá de mostrar un sub-menú.
    # configuring_tariffs = State() 
    # configuring_gamification = State()

@router.message(Command("setup"))
async def start_setup(message: Message, session: AsyncSession):
    """Start the initial setup process for new admins."""
    if not await is_admin(message.from_user.id, session):
        await menu_manager.send_temporary_message(
            message,
            "❌ **Acceso Denegado**\n\nSolo los administradores pueden acceder a la configuración inicial.",
            auto_delete_seconds=5
        )
        return
    
    tenant_service = TenantService(session)
    # Aquí puedes optar por inicializar el tenant o solo verificar el estado
    # Lo dejo como estaba para mantener la compatibilidad con tu lógica de tenant_service
    init_result = await tenant_service.initialize_tenant(message.from_user.id)
    
    if not init_result["success"]:
        await menu_manager.send_temporary_message(
            message,
            f"❌ **Error de Inicialización**\n\n{init_result['error']}",
            auto_delete_seconds=10
        )
        return
    
    # CAMBIO: El comando /setup siempre lleva al menú principal de configuración, no al de elección
    text, keyboard = await menu_factory.create_menu("setup_main", message.from_user.id, session, message.bot)
    await menu_manager.show_menu(
        message,
        text,
        keyboard,
        session,
        "setup_main", # <<<--- SIEMPRE VA A setup_main
        delete_origin_message=True # Añadido: borrar el comando /setup
    )

# --- Channel Handlers ---
@router.callback_query(F.data == "setup_channels")
async def setup_channels_menu(callback: CallbackQuery, session: AsyncSession):
    """Show channel configuration options."""
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer("Acceso denegado", show_alert=True)
    
    text, keyboard = await menu_factory.create_menu("setup_channels", callback.from_user.id, session, callback.bot)
    await menu_manager.update_menu(
        callback,
        text,
        keyboard,
        session,
        "setup_channels"
    )
    await callback.answer()

@router.callback_query(F.data == "setup_vip_channel")
async def setup_vip_channel(callback: CallbackQuery, state: FSMContext, session: AsyncSession): # Añadido session
    """Start VIP channel configuration."""
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer("Acceso denegado", show_alert=True)
    
    text, keyboard = await menu_factory.create_menu("setup_vip_channel_prompt", callback.from_user.id, session, callback.bot)
    await menu_manager.update_menu(
        callback,
        text,
        keyboard,
        session,
        "setup_vip_channel_prompt" # Nuevo estado para el historial
    )
    
    await state.set_state(SetupStates.waiting_for_vip_channel)
    await callback.answer()

@router.callback_query(F.data == "setup_free_channel")
async def setup_free_channel(callback: CallbackQuery, state: FSMContext, session: AsyncSession): # Añadido session
    """Start free channel configuration."""
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer("Acceso denegado", show_alert=True)
    
    text, keyboard = await menu_factory.create_menu("setup_free_channel_prompt", callback.from_user.id, session, callback.bot)
    await menu_manager.update_menu(
        callback,
        text,
        keyboard,
        session,
        "setup_free_channel_prompt" # Nuevo estado para el historial
    )
    
    await state.set_state(SetupStates.waiting_for_free_channel)
    await callback.answer()

@router.callback_query(F.data == "setup_both_channels")
async def setup_both_channels(callback: CallbackQuery, session: AsyncSession):
    """Placeholder for configuring both channels."""
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer("Acceso denegado", show_alert=True)
    
    # Por simplicidad, volvemos al menú de canales y mostramos un mensaje
    # Puedes crear un estado "setup_both_channels_info" en menu_factory
    text = "🛠️ **Configuración de Ambos Canales (Próximamente)**\n\n" \
           "Esta opción te guiará para configurar ambos canales simultáneamente. " \
           "Por ahora, por favor, configúralos individualmente. Gracias."
    await menu_manager.update_menu(
        callback,
        text,
        get_setup_channels_kb(), # Vuelve al teclado de canales
        session,
        "setup_channels" # Mantén el estado del menú de canales
    )
    await callback.answer()

# Handlers para procesamiento de canales reenviados/manuales
@router.message(SetupStates.waiting_for_vip_channel)
async def process_vip_channel(message: Message, state: FSMContext, session: AsyncSession, bot: Bot): # Añadido bot
    """Process VIP channel configuration."""
    if not await is_admin(message.from_user.id, session):
        return
    
    channel_id = None
    channel_title = None
    
    if message.forward_from_chat:
        channel_id = message.forward_from_chat.id
        channel_title = message.forward_from_chat.title
    else:
        # Check if it's a manual ID input
        if message.text and message.text.strip().startswith("-100"): # Los IDs de canal empiezan con -100
             try:
                channel_id = int(message.text.strip())
             except ValueError:
                pass # Se manejará como ID inválido
        
        if not channel_id:
            await menu_manager.send_temporary_message(
                message,
                "❌ **ID Inválido**\n\nPor favor, reenvía un mensaje del canal o ingresa un ID válido.",
                auto_delete_seconds=5
            )
            return await state.set_state(SetupStates.waiting_for_vip_channel) # Volver a esperar
    
    # Store channel info for confirmation
    await state.update_data(
        channel_type="vip",
        channel_id=channel_id,
        channel_title=channel_title,
        message_to_edit_id=message.message_id # Guarda el ID del mensaje del usuario para posible borrado
    )
    
    title_text = f" ({sanitize_text(channel_title)})" if channel_title else ""
    
    # Enviar un nuevo mensaje con la confirmación
    await message.answer(
        f"✅ **Canal VIP Detectado**\n\n"
        f"**ID del Canal**: `{channel_id}`{title_text}\n\n"
        f"¿Es este el canal correcto?",
        reply_markup=get_channel_detection_kb()
    )
    
    await state.set_state(SetupStates.waiting_for_channel_confirmation)

@router.message(SetupStates.waiting_for_free_channel)
async def process_free_channel(message: Message, state: FSMContext, session: AsyncSession, bot: Bot): # Añadido bot
    """Process free channel configuration."""
    if not await is_admin(message.from_user.id, session):
        return
    
    channel_id = None
    channel_title = None
    
    if message.forward_from_chat:
        channel_id = message.forward_from_chat.id
        channel_title = message.forward_from_chat.title
    else:
        # Check if it's a manual ID input
        if message.text and message.text.strip().startswith("-100"):
            try:
                channel_id = int(message.text.strip())
            except ValueError:
                pass
        
        if not channel_id:
            await menu_manager.send_temporary_message(
                message,
                "❌ **ID Inválido**\n\nPor favor, reenvía un mensaje del canal o ingresa un ID válido.",
                auto_delete_seconds=5
            )
            return await state.set_state(SetupStates.waiting_for_free_channel) # Volver a esperar
    
    # Store channel info for confirmation
    await state.update_data(
        channel_type="free",
        channel_id=channel_id,
        channel_title=channel_title,
        message_to_edit_id=message.message_id
    )
    
    title_text = f" ({sanitize_text(channel_title)})" if channel_title else ""
    
    await message.answer(
        f"✅ **Canal Gratuito Detectado**\n\n"
        f"**ID del Canal**: `{channel_id}`{title_text}\n\n"
        f"¿Es este el canal correcto?",
        reply_markup=get_channel_detection_kb()
    )
    
    await state.set_state(SetupStates.waiting_for_channel_confirmation)

# Handlers para botones de confirmación de canal
@router.callback_query(F.data == "confirm_channel", SetupStates.waiting_for_channel_confirmation)
async def confirm_channel_setup(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    """Confirm and save channel configuration."""
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer("Acceso denegado", show_alert=True)
    
    data = await state.get_data()
    channel_type = data.get("channel_type")
    channel_id = data.get("channel_id")
    channel_title = data.get("channel_title")
    
    if not channel_id:
        await callback.answer("Error: No se encontró información del canal", show_alert=True)
        return
    
    tenant_service = TenantService(session)
    
    # Configure the channel
    if channel_type == "vip":
        result = await tenant_service.configure_channels(
            callback.from_user.id,
            vip_channel_id=channel_id,
            channel_titles={"vip": channel_title} if channel_title else None
        )
    else:
        result = await tenant_service.configure_channels(
            callback.from_user.id,
            free_channel_id=channel_id,
            channel_titles={"free": channel_title} if channel_title else None
        )
    
    if result["success"]:
        channel_name = "VIP" if channel_type == "vip" else "Gratuito"
        # Volver al menú principal de setup
        text, keyboard = await menu_factory.create_menu("setup_main", callback.from_user.id, session, callback.bot)
        
        # Opcional: Mostrar un mensaje más específico antes de volver al menú principal
        confirmation_text = f"✅ **Canal {channel_name} Configurado**\n\n" \
                            f"El canal ha sido configurado exitosamente.\n\n" \
                            f"**Siguiente paso**: {text.splitlines()[0]}" # Solo el título del menú principal
        
        await menu_manager.update_menu(
            callback,
            confirmation_text, # Puedes usar el texto que desees aquí
            keyboard,
            session,
            "setup_main"
        )
    else:
        await menu_manager.update_menu( # Usar update_menu en lugar de message.edit_text
            callback,
            f"❌ **Error de Configuración**\n\n{result['error']}",
            get_setup_channels_kb(),
            session,
            "setup_channels"
        )
    
    await state.clear()
    await callback.answer()

@router.callback_query(F.data == "detect_another", SetupStates.waiting_for_channel_confirmation)
async def detect_another_channel(callback: CallbackQuery, state: FSMContext, session: AsyncSession): # Añadido session
    """Allow user to try detecting another channel."""
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer("Acceso denegado", show_alert=True)
    
    data = await state.get_data()
    channel_type = data.get("channel_type")
    
    if channel_type == "vip":
        text, keyboard = await menu_factory.create_menu("setup_vip_channel_prompt", callback.from_user.id, session, callback.bot)
        await menu_manager.update_menu(
            callback,
            text,
            keyboard,
            session,
            "setup_vip_channel_prompt"
        )
        await state.set_state(SetupStates.waiting_for_vip_channel)
    else:
        text, keyboard = await menu_factory.create_menu("setup_free_channel_prompt", callback.from_user.id, session, callback.bot)
        await menu_manager.update_menu(
            callback,
            text,
            keyboard,
            session,
            "setup_free_channel_prompt"
        )
        await state.set_state(SetupStates.waiting_for_free_channel)
    await callback.answer()

@router.callback_query(F.data == "manual_channel_id", SetupStates.waiting_for_channel_confirmation)
async def manual_channel_id_prompt(callback: CallbackQuery, state: FSMContext, session: AsyncSession): # Añadido session
    """Prompt for manual channel ID input."""
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer("Acceso denegado", show_alert=True)
    
    data = await state.get_data()
    channel_type = data.get("channel_type")
    
    text, keyboard = await menu_factory.create_menu("setup_manual_channel_id_prompt", callback.from_user.id, session, callback.bot)
    await menu_manager.update_menu(
        callback,
        f"{text.splitlines()[0]}\n\n{text.splitlines()[2].replace('(empieza con `-100`)', '')} {channel_type.upper()}. Normalment empieza con `-100`.", # Ajusta el texto dinámicamente
        keyboard, # Asumiendo que el teclado es genérico para cancelación
        session,
        "setup_manual_channel_id_prompt"
    )
    await state.set_state(SetupStates.waiting_for_manual_channel_id)
    await callback.answer()

@router.message(SetupStates.waiting_for_manual_channel_id)
async def process_manual_channel_id(message: Message, state: FSMContext, session: AsyncSession, bot: Bot): # Añadido bot
    """Process manually entered channel ID."""
    if not await is_admin(message.from_user.id, session):
        return
    
    try:
        channel_id = int(message.text.strip())
        if not str(channel_id).startswith("-100"): # Validar formato de ID de canal
            raise ValueError("Invalid channel ID format")
            
        data = await state.get_data()
        channel_type = data.get("channel_type")
        
        # Store channel info for confirmation
        await state.update_data(
            channel_id=channel_id,
            channel_title=None, # Manual input usually means no title initially
            message_to_edit_id=message.message_id
        )
        
        await message.answer(
            f"✅ **ID de Canal {channel_type.upper()} Ingresado**\n\n"
            f"**ID del Canal**: `{channel_id}`\n\n"
            f"¿Es este el canal correcto?",
            reply_markup=get_channel_detection_kb()
        )
        await state.set_state(SetupStates.waiting_for_channel_confirmation)
        
    except ValueError:
        await menu_manager.send_temporary_message(
            message,
            "❌ **ID Inválido**\n\nPor favor, ingresa un ID numérico válido para el canal. "
            "Debe empezar con `-100`.",
            auto_delete_seconds=7
        )
        await state.set_state(SetupStates.waiting_for_manual_channel_id) # Volver a esperar
    
# --- Gamification Handlers ---
# setup_gamification_menu ya existe

# setup_default_game ya existe

@router.callback_query(F.data == "setup_missions")
async def setup_missions(callback: CallbackQuery, session: AsyncSession):
    """Handle setup missions click."""
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer("Acceso denegado", show_alert=True)
    
    text, keyboard = await menu_factory.create_menu("setup_missions_info", callback.from_user.id, session, callback.bot)
    await menu_manager.update_menu(
        callback,
        text,
        keyboard,
        session,
        "setup_missions_info" # Nuevo estado para el historial
    )
    await callback.answer()

@router.callback_query(F.data == "setup_badges")
async def setup_badges(callback: CallbackQuery, session: AsyncSession):
    """Handle setup badges click."""
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer("Acceso denegado", show_alert=True)
    
    text, keyboard = await menu_factory.create_menu("setup_badges_info", callback.from_user.id, session, callback.bot)
    await menu_manager.update_menu(
        callback,
        text,
        keyboard,
        session,
        "setup_badges_info"
    )
    await callback.answer()

@router.callback_query(F.data == "setup_rewards")
async def setup_rewards(callback: CallbackQuery, session: AsyncSession):
    """Handle setup rewards click."""
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer("Acceso denegado", show_alert=True)
    
    text, keyboard = await menu_factory.create_menu("setup_rewards_info", callback.from_user.id, session, callback.bot)
    await menu_manager.update_menu(
        callback,
        text,
        keyboard,
        session,
        "setup_rewards_info"
    )
    await callback.answer()

@router.callback_query(F.data == "setup_levels")
async def setup_levels(callback: CallbackQuery, session: AsyncSession):
    """Handle setup levels click."""
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer("Acceso denegado", show_alert=True)
    
    text, keyboard = await menu_factory.create_menu("setup_levels_info", callback.from_user.id, session, callback.bot)
    await menu_manager.update_menu(
        callback,
        text,
        keyboard,
        session,
        "setup_levels_info"
    )
    await callback.answer()

# mybot/handlers/setup.py.txt (Continuación desde "--- Tariff Handlers ---")

# --- Tariff Handlers ---
# setup_tariffs_menu ya existe
# setup_basic_tariff ya existe (que también crea tarifas "premium" por defecto)

@router.callback_query(F.data == "setup_premium_tariff")
async def setup_premium_tariff(callback: CallbackQuery, session: AsyncSession):
    """Handle setup premium tariff click."""
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer("Acceso denegado", show_alert=True)
    
    text, keyboard = await menu_factory.create_menu("setup_premium_tariff_info", callback.from_user.id, session, callback.bot)
    await menu_manager.update_menu(
        callback,
        text,
        keyboard,
        session,
        "setup_premium_tariff_info"
    )
    await callback.answer()

@router.callback_query(F.data == "setup_custom_tariffs")
async def setup_custom_tariffs(callback: CallbackQuery, session: AsyncSession):
    """Handle setup custom tariffs click."""
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer("Acceso denegado", show_alert=True)
    
    text, keyboard = await menu_factory.create_menu("setup_custom_tariffs_info", callback.from_user.id, session, callback.bot)
    await menu_manager.update_menu(
        callback,
        text,
        keyboard,
        session,
        "setup_custom_tariffs_info"
    )
    await callback.answer()


# --- Completion and Navigation Handlers ---

@router.callback_query(F.data == "setup_complete_setup")
async def handle_setup_complete(callback: CallbackQuery, session: AsyncSession, state: FSMContext):
    """Display setup completion message."""
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer("Acceso denegado", show_alert=True)

    await state.clear()

    text, keyboard = await menu_factory.create_menu(
        "setup_complete",
        callback.from_user.id,
        session,
        callback.bot,
    )
    await menu_manager.update_menu(
        callback,
        text,
        keyboard,
        session,
        "setup_complete",
    )
    await callback.answer()


@router.callback_query(F.data == "skip_setup")
async def handle_skip_setup(callback: CallbackQuery, session: AsyncSession, state: FSMContext):
    """Skip remaining setup steps and go directly to the admin panel."""
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer("Acceso denegado", show_alert=True)

    await state.clear()

    text, keyboard = await menu_factory.create_menu(
        "admin_main",
        callback.from_user.id,
        session,
        callback.bot,
    )
    await menu_manager.update_menu(
        callback,
        text,
        keyboard,
        session,
        "admin_main",
    )
    await callback.answer()


@router.callback_query(F.data == "setup_guide")
async def show_setup_guide(callback: CallbackQuery, session: AsyncSession):
    """Show setup guide for admin."""
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer("Acceso denegado", show_alert=True)
    
    text, keyboard = await menu_factory.create_menu("setup_guide_info", callback.from_user.id, session, callback.bot)
    await menu_manager.update_menu(
        callback,
        text,
        keyboard,
        session,
        "setup_guide_info"
    )
    await callback.answer()

@router.callback_query(F.data == "setup_advanced")
async def setup_advanced(callback: CallbackQuery, session: AsyncSession):
    """Handle advanced setup options."""
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer("Acceso denegado", show_alert=True)
    
    text, keyboard = await menu_factory.create_menu("setup_advanced_info", callback.from_user.id, session, callback.bot)
    await menu_manager.update_menu(
        callback,
        text,
        keyboard,
        session,
        "setup_advanced_info"
    )
    await callback.answer()

# Error handlers and cleanup
@router.callback_query(F.data.startswith("cancel_"))
async def cancel_setup_action(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    """Cancel current setup action and return to main setup menu."""
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer("Acceso denegado", show_alert=True)

    await state.clear() # Limpiar el estado de FSM

    text, keyboard = await menu_factory.create_menu("setup_main", callback.from_user.id, session, callback.bot)
    
    await menu_manager.update_menu(
        callback,
        "❌ **Acción Cancelada**\n\n"
        "La configuración ha sido cancelada. Puedes intentar nuevamente cuando quieras.\n\n"
        f"**Siguiente paso**: {text.splitlines()[0]}", # Añade el título del menú principal de setup
        keyboard,
        session,
        "setup_main"
    )
    await callback.answer()

# Handler para el botón "admin_main" en get_setup_complete_kb
@router.callback_query(F.data == "admin_main")
async def navigate_to_admin_main_from_setup(callback: CallbackQuery, session: AsyncSession):
    """Navigate to the main admin panel after setup completion or skip."""
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer("Acceso denegado", show_alert=True)
    
    text, keyboard = await menu_factory.create_menu("admin_main", callback.from_user.id, session, callback.bot)
    await menu_manager.update_menu(
        callback,
        text,
        keyboard,
        session,
        "admin_main"
    )
    await callback.answer()


# --- NUEVOS HANDLERS PARA EL MENÚ DE ELECCIÓN INICIAL DEL ADMINISTRADOR (/start) ---

@router.callback_query(F.data == "start_setup")
async def handle_start_setup_callback(callback: CallbackQuery, session: AsyncSession, state: FSMContext):
    """
    Handles the '🚀 Configurar Ahora' button from the initial admin choice menu.
    Redirects to the main setup menu.
    """
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer("Acceso denegado", show_alert=True)
    
    await state.clear() # Limpia cualquier estado de FSM por si acaso

    text, keyboard = await menu_factory.create_menu("setup_main", callback.from_user.id, session, callback.bot)
    await menu_manager.update_menu(
        callback,
        text,
        keyboard,
        session,
        "setup_main" # Asegúrate de registrar el estado correcto
    )
    await callback.answer()

@router.callback_query(F.data == "skip_to_admin")
async def handle_skip_to_admin_callback(callback: CallbackQuery, session: AsyncSession, state: FSMContext):
    """
    Handles the '⏭️ Ir al Panel' button from the initial admin choice menu.
    Redirects to the main admin panel.
    """
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer("Acceso denegado", show_alert=True)
    
    await state.clear() # Limpia cualquier estado de FSM por si acaso

    text, keyboard = await menu_factory.create_menu("admin_main", callback.from_user.id, session, callback.bot)
    await menu_manager.update_menu(
        callback,
        text,
        keyboard,
        session,
        "admin_main" # Asegúrate de registrar el estado correcto
    )
    await callback.answer()

@router.callback_query(F.data == "show_setup_guide")
async def handle_show_setup_guide_callback(callback: CallbackQuery, session: AsyncSession, state: FSMContext):
    """
    Handles the '📖 Ver Guía' button from the initial admin choice menu.
    Redirects to the setup guide menu.
    """
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer("Acceso denegado", show_alert=True)
    
    await state.clear() # Limpia cualquier estado de FSM por si acaso

    text, keyboard = await menu_factory.create_menu("setup_guide_info", callback.from_user.id, session, callback.bot)
    await menu_manager.update_menu(
        callback,
        text,
        keyboard,
        session,
        "setup_guide_info" # Asegúrate de registrar el estado correcto
    )
    await callback.answer()

# --- HANDLER PARA EL BOTÓN "JUEGO KINKY" EN EL MENÚ DE ADMINISTRACIÓN ---

@router.callback_query(F.data == "admin_kinky_game") # Asumiendo este callback_data para el menú de administración
async def handle_admin_kinky_game_button(callback: CallbackQuery, session: AsyncSession):
    """
    Handles the 'Juego Kinky' button click from the admin panel.
    Displays the Kinky Game menu or info for admins.
    """
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer("Acceso denegado", show_alert=True)
    
    from utils.keyboard_utils import get_admin_manage_content_keyboard # Asegurarse de la importación
    
    text = "🎲 **Panel de Gestión de Gamificación Kinky**\n\n" \
           "¡Bienvenido al centro de control de todos tus juegos y actividades! " \
           "Aquí puedes gestionar usuarios, misiones, recompensas y más. " \
           "Elige lo que quieres hacer:"
    
    keyboard = get_admin_manage_content_keyboard()
    
    await menu_manager.update_menu(
        callback,
        text,
        keyboard,
        session,
        "admin_gamification_main" # Usamos este estado, ya que es el menú de gamificación general
    )
    await callback.answer()
