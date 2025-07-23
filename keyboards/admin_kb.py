from aiogram.utils.keyboard import InlineKeyboardBuilder


def get_admin_kb():
    """Return a minimal admin menu."""

    builder = InlineKeyboardBuilder()
    # Single button for the admin menu
    builder.button(text="Botón de administración", callback_data="admin_button")
    return builder.as_markup()
