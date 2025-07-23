from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardMarkup


def get_packs_list_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="💫 Encanto Inicial – $150 MXN", callback_data="pack_1")
    builder.button(text="🔥 Sensualidad Revelada – $200 MXN", callback_data="pack_2")
    builder.button(text="💋 Pasión Desbordante – $250 MXN", callback_data="pack_3")
    builder.button(text="🔞 Intimidad Explosiva – $300 MXN", callback_data="pack_4")
    builder.button(text="🔙 Volver", callback_data="free_main_menu")
    builder.adjust(1)
    return builder.as_markup()


def get_pack_detail_kb(pack_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="Me interesa 🔥", callback_data=f"pack_interest_{pack_id}")
    builder.button(text="🔙 Regresar", callback_data="free_packs")
    builder.adjust(1)
    return builder.as_markup()
