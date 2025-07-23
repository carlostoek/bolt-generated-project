# constants/keyboards.py
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

main_menu_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="🎒 Mochila"),
            KeyboardButton(text="💰 Billetera"),
            KeyboardButton(text="🎯 Misiones"),
        ],
        [
            KeyboardButton(text="⚙️ Configuración"),
            KeyboardButton(text="❓ Ayuda"),
        ],
    ],
    resize_keyboard=True,
    one_time_keyboard=False,
)
