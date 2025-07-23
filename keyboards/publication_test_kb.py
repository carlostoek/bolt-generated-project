from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardMarkup


def get_publication_test_kb() -> InlineKeyboardMarkup:
    """Keyboard with a single confirm button for the publication test."""
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Confirmar", callback_data="confirmar_test_publicacion")
    builder.adjust(1)
    return builder.as_markup()


def get_publication_test_completed_kb() -> InlineKeyboardMarkup:
    """Keyboard shown once the test is confirmed."""
    builder = InlineKeyboardBuilder()
    builder.button(text="Test completado", callback_data="test_done")
    builder.adjust(1)
    return builder.as_markup()
