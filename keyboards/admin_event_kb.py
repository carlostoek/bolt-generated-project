from aiogram.utils.keyboard import InlineKeyboardBuilder


def get_admin_event_main_kb():
    builder = InlineKeyboardBuilder()
    builder.button(text="⚡ Eventos", callback_data="event_menu")
    builder.button(text="🎟 Sorteos", callback_data="raffle_menu")
    builder.button(text="🔙 Volver", callback_data="admin_main_menu")
    builder.adjust(1)
    return builder.as_markup()


def get_event_menu_kb():
    builder = InlineKeyboardBuilder()
    builder.button(text="➕ Crear Evento", callback_data="create_event")
    builder.button(text="📃 Eventos Activos", callback_data="list_events")
    builder.button(text="⛔ Finalizar Evento", callback_data="end_event")
    builder.button(text="🔙 Volver", callback_data="admin_manage_events_sorteos")
    builder.adjust(1)
    return builder.as_markup()


def get_raffle_menu_kb():
    builder = InlineKeyboardBuilder()
    builder.button(text="➕ Crear Sorteo", callback_data="create_raffle")
    builder.button(text="📃 Sorteos Activos", callback_data="list_raffles")
    builder.button(text="🏁 Finalizar Sorteo", callback_data="end_raffle")
    builder.button(text="🔙 Volver", callback_data="admin_manage_events_sorteos")
    builder.adjust(1)
    return builder.as_markup()
