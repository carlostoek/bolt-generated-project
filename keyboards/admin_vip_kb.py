from aiogram.utils.keyboard import InlineKeyboardBuilder


def get_admin_vip_kb() -> InlineKeyboardBuilder:
    builder = InlineKeyboardBuilder()
    builder.button(text="📊 Estadísticas", callback_data="vip_stats")
    builder.button(text="🔑 Generar Token", callback_data="vip_generate_token")
    builder.button(text="👥 Suscriptores", callback_data="vip_manage")
    builder.button(text="🏅 Asignar Insignia", callback_data="vip_manual_badge")
    builder.button(text="📝 Publicar Canal", callback_data="admin_send_channel_post")
    builder.button(text="⚙️ Configuración", callback_data="vip_config")
    builder.button(text="🔄 Actualizar", callback_data="admin_vip")
    builder.button(text="↩️ Volver", callback_data="admin_back")
    builder.adjust(2, 2, 2, 2)
    return builder.as_markup()
