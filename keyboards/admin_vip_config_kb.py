from aiogram.utils.keyboard import InlineKeyboardBuilder


def get_admin_vip_config_kb():
    builder = InlineKeyboardBuilder()
    builder.button(text="💰 Tarifas", callback_data="config_tarifas")
    builder.button(text="✉️ Mensajes", callback_data="vip_config_messages")
    builder.button(text="🔄 Actualizar", callback_data="admin_vip_config")
    builder.button(text="↩️ Volver", callback_data="admin_vip")
    builder.adjust(2, 2)
    return builder.as_markup()


def get_tariff_select_kb(tariffs):
    builder = InlineKeyboardBuilder()
    for tariff in tariffs:
        builder.button(text=tariff.name, callback_data=f"generate_token_{tariff.id}")
    builder.button(text="↩️ Volver", callback_data="admin_vip")
    builder.adjust(2)
    return builder.as_markup()


def get_vip_messages_kb():
    builder = InlineKeyboardBuilder()
    builder.button(text="📣 Recordatorio", callback_data="edit_vip_reminder")
    builder.button(text="👋 Despedida", callback_data="edit_vip_farewell")
    builder.button(text="↩️ Volver", callback_data="vip_config")
    builder.adjust(2)
    return builder.as_markup()
