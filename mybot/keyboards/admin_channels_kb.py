from aiogram.utils.keyboard import InlineKeyboardBuilder


def get_admin_channels_kb(channels: list | None = None):
    builder = InlineKeyboardBuilder()
    if channels:
        for channel in channels:
            label = channel.title or str(channel.id)
            builder.button(text=f"❌ {label}", callback_data=f"remove_channel_{channel.id}")
    builder.button(text="➕ Agregar Canal", callback_data="admin_add_channel")
    builder.button(text="⏱ Configurar Espera", callback_data="admin_wait_time")
    builder.button(text="🔙 Volver", callback_data="admin_back")
    builder.adjust(1)
    return builder.as_markup()


def get_wait_time_kb():
    builder = InlineKeyboardBuilder()
    options = [0, 5, 10, 15, 20, 60, 120, 180]
    for m in options:
        label = f"{m} min" if m < 60 else f"{m//60} h"
        if m == 0:
            label = "0 min"
        builder.button(text=label, callback_data=f"wait_{m}")
    builder.button(text="🔙 Volver", callback_data="admin_channels")
    builder.adjust(3)
    return builder.as_markup()
