from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardMarkup


def get_save_and_cancel_kb() -> InlineKeyboardMarkup:
    """Returns a keyboard with 'Save' and 'Cancel' buttons for configuration flows."""
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Guardar", callback_data="save_reactions")
    builder.button(text="❌ Cancelar", callback_data="cancel_config")
    builder.adjust(2)
    return builder.as_markup()
