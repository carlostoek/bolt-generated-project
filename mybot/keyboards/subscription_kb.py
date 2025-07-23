# mybot/keyboards/suscripcion_kb.py
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardMarkup

def get_free_main_menu_kb() -> InlineKeyboardMarkup:
    """Return the main menu keyboard for free users."""
    builder = InlineKeyboardBuilder()
    builder.button(text="🎁 Desbloquear Regalo", callback_data="free_gift")
    builder.button(text="🎀 Mis Packs", callback_data="free_packs")
    builder.button(text="🔐 Explorar VIP", callback_data="free_vip_explore")
    builder.button(text="💌 Contenido Custom", callback_data="free_custom")
    builder.button(text="🎮 Juego Kinky", callback_data="free_game")
    builder.button(text="🌐 Sígueme", callback_data="free_follow")
    builder.adjust(2, 2, 2)
    return builder.as_markup()

def get_vip_explore_kb() -> InlineKeyboardMarkup:
    """Keyboard shown in the free VIP explore section."""
    builder = InlineKeyboardBuilder()
    builder.button(text="🔥 Me Interesa", callback_data="vip_explore_interest")
    builder.button(text="↩️ Regresar", callback_data="free_main_menu")
    builder.adjust(2)
    return builder.as_markup()

def get_subscription_kb() -> InlineKeyboardMarkup:
    """Alias for backward compatibility."""
    return get_free_main_menu_kb()

def get_free_info_kb() -> InlineKeyboardMarkup:
    """Keyboard shown in the information section."""
    builder = InlineKeyboardBuilder()
    builder.button(text="❓ FAQ", callback_data="free_info_faq")
    builder.button(text="📢 Novedades", callback_data="free_info_news")
    builder.button(text="↩️ Menú Principal", callback_data="free_main")
    builder.adjust(2, 1)
    return builder.as_markup()

def get_free_game_kb() -> InlineKeyboardMarkup:
    """Keyboard shown in the free mini game section."""
    builder = InlineKeyboardBuilder()
    builder.button(text="🎮 Jugar", callback_data="free_game_play")
    builder.button(text="🏆 Puntuación", callback_data="free_game_score")
    builder.button(text="↩️ Menú Principal", callback_data="free_main")
    builder.adjust(2, 1)
    return builder.as_markup()
