from aiogram.types import InlineKeyboardButton


def get_pagination_buttons(page: int, total_pages: int, prefix: str) -> list[InlineKeyboardButton]:
    """Return navigation buttons for a paginated list."""
    buttons: list[InlineKeyboardButton] = []
    if page > 0:
        buttons.append(InlineKeyboardButton(text="⬅️", callback_data=f"{prefix}:{page-1}"))
    if page + 1 < total_pages:
        buttons.append(InlineKeyboardButton(text="➡️", callback_data=f"{prefix}:{page+1}"))
    return buttons
