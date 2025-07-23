from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def trivia_admin_main_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📖 Listar Trivias", callback_data="list_trivias")],
        [InlineKeyboardButton(text="➕ Crear Nueva Trivia", callback_data="create_trivia")]
    ])


def question_type_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📝 Abierta", callback_data="open")],
        [InlineKeyboardButton(text="🔘 Opciones múltiples", callback_data="multiple")]
    ])


def yes_no_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Sí", callback_data="yes"), InlineKeyboardButton(text="❌ No", callback_data="no")]
    ])


def confirm_trivia_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Confirmar", callback_data="confirm")],
        [InlineKeyboardButton(text="❌ Cancelar", callback_data="cancel")]
    ])
