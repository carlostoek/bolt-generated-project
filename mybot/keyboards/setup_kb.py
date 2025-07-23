"""
Keyboards for initial bot setup and multi-tenant configuration.
"""
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardMarkup

def get_setup_main_kb() -> InlineKeyboardMarkup:
    """Main setup menu for new bot installations."""
    builder = InlineKeyboardBuilder()
    builder.button(text="📢 Configurar Canales", callback_data="setup_channels")
    builder.button(text="🎮 Configurar Gamificación", callback_data="setup_gamification")
    builder.button(text="💳 Configurar Tarifas VIP", callback_data="setup_tariffs")
    builder.button(text="✅ Finalizar Configuración", callback_data="setup_complete_setup")
    builder.button(text="⏭️ Omitir Configuración", callback_data="skip_setup")
    builder.adjust(1)
    return builder.as_markup()

def get_setup_channels_kb() -> InlineKeyboardMarkup:
    """Channel setup keyboard."""
    builder = InlineKeyboardBuilder()
    builder.button(text="🔐 Configurar Canal VIP", callback_data="setup_vip_channel")
    builder.button(text="🆓 Configurar Canal Gratuito", callback_data="setup_free_channel")
    builder.button(text="📋 Configurar Ambos", callback_data="setup_both_channels")
    builder.button(text="⏭️ Omitir por Ahora", callback_data="setup_main")
    builder.button(text="🔙 Volver", callback_data="setup_main")
    builder.adjust(1)
    return builder.as_markup()

def get_setup_gamification_kb() -> InlineKeyboardMarkup:
    """Gamification setup keyboard."""
    builder = InlineKeyboardBuilder()
    builder.button(text="🎯 Configurar Misiones", callback_data="setup_missions")
    builder.button(text="🏅 Configurar Insignias", callback_data="setup_badges")
    builder.button(text="🎁 Configurar Recompensas", callback_data="setup_rewards")
    builder.button(text="📊 Configurar Niveles", callback_data="setup_levels")
    builder.button(text="✅ Usar Configuración por Defecto", callback_data="setup_default_game")
    builder.button(text="🔙 Volver", callback_data="setup_main")
    builder.adjust(1)
    return builder.as_markup()

def get_setup_tariffs_kb() -> InlineKeyboardMarkup:
    """Tariff setup keyboard."""
    builder = InlineKeyboardBuilder()
    builder.button(text="💎 Crear Tarifa Básica", callback_data="setup_basic_tariff")
    builder.button(text="👑 Crear Tarifa Premium", callback_data="setup_premium_tariff")
    builder.button(text="🎯 Configuración Personalizada", callback_data="setup_custom_tariffs")
    builder.button(text="⏭️ Configurar Más Tarde", callback_data="setup_main")
    builder.button(text="🔙 Volver", callback_data="setup_main")
    builder.adjust(1)
    return builder.as_markup()

def get_setup_complete_kb() -> InlineKeyboardMarkup:
    """Setup completion keyboard."""
    builder = InlineKeyboardBuilder()
    builder.button(text="🛠️ Ir al Panel de Admin", callback_data="admin_main")
    builder.button(text="📖 Ver Guía de Uso", callback_data="setup_guide")
    builder.button(text="🔧 Configuración Avanzada", callback_data="setup_advanced")
    builder.adjust(1)
    return builder.as_markup()

def get_channel_detection_kb() -> InlineKeyboardMarkup:
    """Keyboard for channel ID detection."""
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Confirmar Canal", callback_data="confirm_channel")
    builder.button(text="🔄 Detectar Otro", callback_data="detect_another")
    builder.button(text="✏️ Ingresar Manualmente", callback_data="manual_channel_id")
    builder.button(text="🔙 Volver", callback_data="setup_channels")
    builder.adjust(1)
    return builder.as_markup()

def get_setup_confirmation_kb(action: str) -> InlineKeyboardMarkup:
    """Generic confirmation keyboard for setup actions."""
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Confirmar", callback_data=f"confirm_{action}")
    builder.button(text="❌ Cancelar", callback_data="setup_main")
    builder.adjust(1)
    return builder.as_markup()
