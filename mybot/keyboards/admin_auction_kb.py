from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardMarkup


def get_admin_auction_main_kb():
    """Main auction management keyboard."""
    builder = InlineKeyboardBuilder()
    builder.button(text="➕ Crear Subasta", callback_data="admin_create_auction")
    builder.button(text="📋 Subastas Activas", callback_data="admin_list_active_auctions")
    builder.button(text="📊 Subastas Pendientes", callback_data="admin_list_pending_auctions")
    builder.button(text="🏁 Finalizar Subasta", callback_data="admin_end_auction")
    builder.button(text="❌ Cancelar Subasta", callback_data="admin_cancel_auction")
    builder.button(text="📈 Estadísticas", callback_data="admin_auction_stats")
    builder.button(text="🔙 Volver", callback_data="admin_manage_content")
    builder.adjust(1)
    return builder.as_markup()


def get_auction_duration_kb():
    """Keyboard for selecting auction duration."""
    builder = InlineKeyboardBuilder()
    builder.button(text="1 hora", callback_data="auction_duration_1")
    builder.button(text="3 horas", callback_data="auction_duration_3")
    builder.button(text="6 horas", callback_data="auction_duration_6")
    builder.button(text="12 horas", callback_data="auction_duration_12")
    builder.button(text="24 horas", callback_data="auction_duration_24")
    builder.button(text="48 horas", callback_data="auction_duration_48")
    builder.button(text="72 horas", callback_data="auction_duration_72")
    builder.button(text="🔙 Cancelar", callback_data="admin_auction_main")
    builder.adjust(2)
    return builder.as_markup()


def get_auction_settings_kb():
    """Keyboard for auction advanced settings."""
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Configuración Básica", callback_data="auction_basic_settings")
    builder.button(text="⚙️ Configuración Avanzada", callback_data="auction_advanced_settings")
    builder.button(text="🔙 Volver", callback_data="admin_auction_main")
    builder.adjust(1)
    return builder.as_markup()


def get_auction_confirmation_kb(auction_data: dict):
    """Keyboard for confirming auction creation."""
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Crear Subasta", callback_data="confirm_create_auction")
    builder.button(text="✏️ Editar", callback_data="edit_auction_data")
    builder.button(text="❌ Cancelar", callback_data="admin_auction_main")
    builder.adjust(1)
    return builder.as_markup()


def get_auction_list_kb(auctions: list, action_prefix: str = "view"):
    """Keyboard for listing auctions with actions."""
    builder = InlineKeyboardBuilder()
    
    for auction in auctions:
        status_emoji = {
            'pending': '⏳',
            'active': '🔥',
            'ended': '🏁',
            'cancelled': '❌'
        }.get(auction.status.value, '❓')
        
        button_text = f"{status_emoji} {auction.name}"
        callback_data = f"{action_prefix}_auction_{auction.id}"
        builder.button(text=button_text, callback_data=callback_data)
    
    builder.button(text="🔙 Volver", callback_data="admin_auction_main")
    builder.adjust(1)
    return builder.as_markup()


def get_auction_action_kb(auction_id: int, auction_status: str):
    """Keyboard for individual auction actions."""
    builder = InlineKeyboardBuilder()
    
    if auction_status == 'active':
        builder.button(text="🏁 Finalizar", callback_data=f"end_auction_{auction_id}")
        builder.button(text="❌ Cancelar", callback_data=f"cancel_auction_{auction_id}")
    elif auction_status == 'pending':
        builder.button(text="▶️ Iniciar", callback_data=f"start_auction_{auction_id}")
        builder.button(text="❌ Cancelar", callback_data=f"cancel_auction_{auction_id}")
    
    builder.button(text="📊 Ver Detalles", callback_data=f"view_auction_details_{auction_id}")
    builder.button(text="🔙 Volver", callback_data="admin_auction_main")
    builder.adjust(1)
    return builder.as_markup()


def get_auction_confirm_action_kb(action: str, auction_id: int):
    """Keyboard for confirming auction actions."""
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Confirmar", callback_data=f"confirm_{action}_auction_{auction_id}")
    builder.button(text="❌ Cancelar", callback_data=f"view_auction_{auction_id}")
    builder.adjust(1)
    return builder.as_markup()
