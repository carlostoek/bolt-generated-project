"""Keyboard helpers for VIP menus."""

from utils.keyboard_utils import get_main_menu_keyboard


def get_vip_main_kb():
    """Return the default VIP menu keyboard.

    This mirrors the menu previously shown under "Juego Kinky" so that
    VIP users immediately see all options like Mi Suscripción, Perfil y
    Misiones al entrar.
    """

    return get_main_menu_keyboard()
