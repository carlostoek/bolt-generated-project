from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardMarkup


def get_admin_vip_channel_kb() -> InlineKeyboardMarkup:
    """Returns the keyboard for the VIP Channel admin menu."""
    builder = InlineKeyboardBuilder()
    builder.button(text="📊 Estadísticas", callback_data="vip_stats")
    builder.button(text="🔑 Generar Token", callback_data="vip_generate_token")
    builder.button(text="👥 Suscriptores", callback_data="vip_manage")
    builder.button(text="🏅 Asignar Insignia", callback_data="vip_manual_badge")
    builder.button(text="📝 Publicar Canal", callback_data="admin_send_channel_post")
    builder.button(text="⚙️ Configuración", callback_data="vip_config")
    builder.button(text="💋 Config Reacciones", callback_data="vip_config_reactions")
    builder.button(text="🔄 Actualizar", callback_data="admin_vip_channel")
    builder.button(text="↩️ Volver", callback_data="admin_main")
    builder.adjust(2, 2, 2, 2, 1)
    return builder.as_markup()
