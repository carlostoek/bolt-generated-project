from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def trivia_selection_keyboard(trivias):
    buttons = [[InlineKeyboardButton(text=t.title, callback_data=f"start_trivia:{t.id}")]
               for t in trivias]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def trivia_question_keyboard(options):
    buttons = [[InlineKeyboardButton(text=v, callback_data=f"answer:{k}")]
               for k, v in options.items()]
    return InlineKeyboardMarkup(inline_keyboard=buttons)
