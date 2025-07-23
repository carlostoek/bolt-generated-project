from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardMarkup
from utils.text_utils import format_points


def get_auction_main_kb():
    """Main auction menu for users."""
    builder = InlineKeyboardBuilder()
    builder.button(text="🔥 Subastas Activas", callback_data="view_active_auctions")
    builder.button(text="📋 Mis Subastas", callback_data="view_my_auctions")
    builder.button(text="🏆 Historial", callback_data="view_auction_history")
    builder.button(text="🔙 Volver", callback_data="menu_principal")
    builder.adjust(1)
    return builder.as_markup()


def get_auction_list_kb(auctions: list, page: int = 0, per_page: int = 5):
    """Keyboard for listing auctions with pagination."""
    builder = InlineKeyboardBuilder()
    
    start_idx = page * per_page
    end_idx = start_idx + per_page
    page_auctions = auctions[start_idx:end_idx]
    
    for auction in page_auctions:
        status_emoji = {
            'pending': '⏳',
            'active': '🔥',
            'ended': '🏁',
            'cancelled': '❌'
        }.get(auction.status.value, '❓')
        
        button_text = f"{status_emoji} {auction.name}"
        if auction.current_highest_bid > 0:
            button_text += f" ({auction.current_highest_bid}pts)"
        
        builder.button(text=button_text, callback_data=f"view_auction_{auction.id}")
    
    # Pagination buttons
    nav_buttons = []
    if page > 0:
        nav_buttons.append(("⬅️ Anterior", f"auction_page_{page-1}"))
    if end_idx < len(auctions):
        nav_buttons.append(("Siguiente ➡️", f"auction_page_{page+1}"))
    
    if nav_buttons:
        for text, callback in nav_buttons:
            builder.button(text=text, callback_data=callback)
    
    builder.button(text="🔙 Volver", callback_data="auction_main")
    builder.adjust(1)
    return builder.as_markup()


def get_auction_details_kb(auction_id: int, is_participating: bool, auction_status: str, user_can_bid: bool = True):
    """Keyboard for auction details view."""
    builder = InlineKeyboardBuilder()
    
    if auction_status == 'active' and user_can_bid:
        builder.button(text="💰 Hacer Puja", callback_data=f"place_bid_{auction_id}")
    
    if is_participating:
        builder.button(text="🔔 Notificaciones", callback_data=f"toggle_notifications_{auction_id}")
    
    builder.button(text="🔄 Actualizar", callback_data=f"view_auction_{auction_id}")
    builder.button(text="📊 Ver Pujas", callback_data=f"view_bids_{auction_id}")
    builder.button(text="🔙 Volver", callback_data="view_active_auctions")
    builder.adjust(1)
    return builder.as_markup()


def get_bid_amount_kb(min_bid: int):
    """Keyboard for quick bid amounts."""
    builder = InlineKeyboardBuilder()
    
    # Quick bid options
    quick_bids = [
        min_bid,
        min_bid + 10,
        min_bid + 25,
        min_bid + 50,
        min_bid + 100
    ]
    
    for amount in quick_bids:
        builder.button(text=f"{amount} pts", callback_data=f"quick_bid_{amount}")
    
    builder.button(text="✏️ Cantidad Personalizada", callback_data="custom_bid_amount")
    builder.button(text="🔙 Cancelar", callback_data="cancel_bid")
    builder.adjust(2)
    return builder.as_markup()


def get_bid_confirmation_kb(auction_id: int, amount: int):
    """Keyboard for confirming a bid."""
    builder = InlineKeyboardBuilder()
    builder.button(text=f"✅ Confirmar {amount} pts", callback_data=f"confirm_bid_{auction_id}_{amount}")
    builder.button(text="❌ Cancelar", callback_data=f"view_auction_{auction_id}")
    builder.adjust(1)
    return builder.as_markup()


def get_auction_notifications_kb(auction_id: int, enabled: bool):
    """Keyboard for managing auction notifications."""
    builder = InlineKeyboardBuilder()
    
    if enabled:
        builder.button(text="🔕 Desactivar Notificaciones", callback_data=f"disable_notifications_{auction_id}")
    else:
        builder.button(text="🔔 Activar Notificaciones", callback_data=f"enable_notifications_{auction_id}")
    
    builder.button(text="🔙 Volver", callback_data=f"view_auction_{auction_id}")
    builder.adjust(1)
    return builder.as_markup()


def get_bid_history_kb(auction_id: int, page: int = 0):
    """Keyboard for bid history pagination."""
    builder = InlineKeyboardBuilder()
    
    if page > 0:
        builder.button(text="⬅️ Anterior", callback_data=f"bid_history_{auction_id}_{page-1}")
    
    builder.button(text="Siguiente ➡️", callback_data=f"bid_history_{auction_id}_{page+1}")
    builder.button(text="🔙 Volver", callback_data=f"view_auction_{auction_id}")
    builder.adjust(1)
    return builder.as_markup()
