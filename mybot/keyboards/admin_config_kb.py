from aiogram.utils.keyboard import InlineKeyboardBuilder


def get_admin_config_kb():
    builder = InlineKeyboardBuilder()
    builder.button(text="📺 Agregar Canales", callback_data="config_add_channels")
    builder.button(text="⏱️ Schedulers", callback_data="config_scheduler")
    builder.button(text="🔄 Actualizar", callback_data="admin_config")
    builder.button(text="↩️ Volver", callback_data="admin_back")
    builder.adjust(2, 2)
    return builder.as_markup()


def get_channel_type_kb():
    """Keyboard to choose which channels to configure."""
    builder = InlineKeyboardBuilder()
    builder.button(text="💎 Solo VIP", callback_data="channel_mode_vip")
    builder.button(text="💬 Solo FREE", callback_data="channel_mode_free")
    builder.button(text="🔗 Ambos Canales", callback_data="channel_mode_both")
    builder.button(text="↩️ Volver", callback_data="admin_config")
    builder.adjust(2, 1, 1)
    return builder.as_markup()


def get_scheduler_config_kb():
    builder = InlineKeyboardBuilder()
    builder.button(text="⏲ Canal General", callback_data="set_channel_interval")
    builder.button(text="⏲ Canal VIP", callback_data="set_vip_interval")
    builder.button(text="▶️ Ejecutar Ahora", callback_data="run_schedulers_now")
    builder.button(text="↩️ Volver", callback_data="admin_config")
    builder.adjust(2, 1, 1)
    return builder.as_markup()


def get_config_done_kb():
    """Keyboard shown when channel configuration finishes."""
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Aceptar", callback_data="admin_config")
    builder.button(text="🏠 Menú Principal", callback_data="admin_back")
    builder.adjust(2)
    return builder.as_markup()


def get_reaction_confirm_kb():
    """Keyboard shown while configuring reaction emojis."""
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Guardar", callback_data="save_reactions")
    builder.button(text="↩️ Volver", callback_data="admin_config")
    builder.adjust(2)
    return builder.as_markup()
