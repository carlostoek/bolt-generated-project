from aiogram.utils.keyboard import InlineKeyboardBuilder


def get_admin_main_kb():
    """Return the main admin inline keyboard with elegant layout."""
    builder = InlineKeyboardBuilder()
    
    # Fila 1: Gestión de canales principales
    builder.button(text="💎 Canal VIP", callback_data="admin_vip")
    builder.button(text="💬 Canal Free", callback_data="admin_free")
    
    # Fila 2: Entretenimiento y juegos
    builder.button(text="🎮 Juego Kinky", callback_data="admin_kinky_game")
    builder.button(text="📊 Estadísticas", callback_data="admin_stats")
    
    # Fila 3: Configuración y navegación
    builder.button(text="⚙️ Configuración", callback_data="admin_config")
    builder.button(text="🔄 Actualizar", callback_data="admin_main_menu")
    
    # Fila 4: Navegación
    builder.button(text="↩️ Volver", callback_data="admin_back")
    
    # Distribución: 2x2, luego 2x1, luego 1
    builder.adjust(2, 2, 2, 1)
    return builder.as_markup()
