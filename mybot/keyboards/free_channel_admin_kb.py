"""
Teclados para administración del canal gratuito.
"""
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardMarkup


def get_free_channel_admin_kb(channel_configured: bool = False) -> InlineKeyboardMarkup:
    """Teclado principal para administración del canal gratuito."""
    builder = InlineKeyboardBuilder()
    
    if channel_configured:
        builder.button(text="⏰ Tiempo Espera", callback_data="set_wait_time")
        builder.button(text="🔗 Crear Enlace", callback_data="create_invite_link")
        builder.button(text="📝 Enviar Contenido", callback_data="send_to_free_channel")
        builder.button(text="⚡ Procesar Ahora", callback_data="process_pending_now")
        builder.button(text="🧹 Limpiar Antiguas", callback_data="cleanup_old_requests")
        builder.button(text="📊 Estadísticas", callback_data="free_channel_stats")
        builder.button(text="💋 Config Reacciones", callback_data="free_config_reactions")
        builder.button(text="🔄 Actualizar", callback_data="admin_free_channel")
    else:
        builder.button(text="⚙️ Configurar Canal", callback_data="configure_free_channel")
    
    builder.button(text="↩️ Volver", callback_data="admin_main_menu")
    builder.adjust(2, 2, 2, 2, 1)
    return builder.as_markup()


def get_wait_time_selection_kb() -> InlineKeyboardMarkup:
    """Teclado para seleccionar tiempo de espera."""
    builder = InlineKeyboardBuilder()
    
    times = [
        (0, "⚡ Inmediato"),
        (5, "⏱️ 5 min"),
        (15, "🕐 15 min"),
        (30, "🕕 30 min"),
        (60, "⏰ 1 hora"),
        (120, "🕑 2 horas"),
        (360, "🕕 6 horas"),
        (720, "🕛 12 horas"),
        (1440, "📅 24 horas")
    ]
    
    for minutes, label in times:
        builder.button(text=label, callback_data=f"wait_time_{minutes}")
    
    builder.button(text="↩️ Volver", callback_data="admin_free_channel")
    builder.adjust(2, 2, 2, 2, 2, 1)
    return builder.as_markup()


def get_channel_post_options_kb() -> InlineKeyboardMarkup:
    """Teclado para opciones de publicación en canal."""
    builder = InlineKeyboardBuilder()
    
    builder.button(text="📎 Agregar Media", callback_data="add_media")
    builder.button(text="➡️ Sin Media", callback_data="continue_without_media")
    builder.button(text="❌ Cancelar", callback_data="admin_free_channel")
    
    builder.adjust(2, 1)
    return builder.as_markup()


def get_content_protection_kb() -> InlineKeyboardMarkup:
    """Teclado para configurar protección de contenido."""
    builder = InlineKeyboardBuilder()
    
    builder.button(text="🔒 Proteger", callback_data="protect_yes")
    builder.button(text="🔓 Libre", callback_data="protect_no")
    builder.button(text="❌ Cancelar", callback_data="admin_free_channel")
    
    builder.adjust(2, 1)
    return builder.as_markup()


def get_invite_link_options_kb() -> InlineKeyboardMarkup:
    """Teclado para opciones de enlace de invitación."""
    builder = InlineKeyboardBuilder()
    
    builder.button(text="📋 Enlace Estándar", callback_data="create_standard_link")
    builder.button(text="⏰ Enlace Temporal", callback_data="create_temporary_link")
    builder.button(text="👥 Enlace Limitado", callback_data="create_limited_link")
    builder.button(text="↩️ Volver", callback_data="admin_free_channel")
    
    builder.adjust(2, 1, 1)
    return builder.as_markup()
