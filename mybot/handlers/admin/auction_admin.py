from aiogram import Router, F, Bot
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime, timedelta

from utils.user_roles import is_admin
from utils.menu_utils import update_menu, send_temporary_reply
from utils.admin_state import AdminAuctionStates
from keyboards.admin_auction_kb import (
    get_admin_auction_main_kb,
    get_auction_duration_kb,
    get_auction_settings_kb,
    get_auction_confirmation_kb,
    get_auction_list_kb,
    get_auction_action_kb,
    get_auction_confirm_action_kb
)
from keyboards.common import get_back_kb
from services.auction_service import AuctionService
from utils.text_utils import format_time_remaining, format_points, anonymize_username
import logging

logger = logging.getLogger(__name__)
router = Router()


@router.callback_query(F.data == "admin_auction_main")
async def admin_auction_main(callback: CallbackQuery, session: AsyncSession):
    """Main auction administration menu."""
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer()
    
    await update_menu(
        callback,
        "🏛️ **Administración de Subastas**\n\nGestiona las subastas en tiempo real del sistema.",
        get_admin_auction_main_kb(),
        session,
        "admin_auction_main",
    )
    await callback.answer()


@router.callback_query(F.data == "admin_create_auction")
async def start_create_auction(callback: CallbackQuery, state: FSMContext):
    """Start auction creation flow."""
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer()
    
    await callback.message.edit_text(
        "📝 **Crear Nueva Subasta**\n\nIngresa el nombre de la subasta:",
        reply_markup=get_back_kb("admin_auction_main")
    )
    await state.set_state(AdminAuctionStates.creating_auction_name)
    await callback.answer()


@router.message(AdminAuctionStates.creating_auction_name)
async def process_auction_name(message: Message, state: FSMContext):
    """Process auction name input."""
    if not await is_admin(message.from_user.id, session):
        return
    
    name = message.text.strip()
    if len(name) < 3:
        await send_temporary_reply(message, "❌ El nombre debe tener al menos 3 caracteres.")
        return
    
    await state.update_data(name=name)
    await message.answer(
        f"✅ Nombre: **{name}**\n\n📝 Ahora ingresa una descripción para la subasta:",
        reply_markup=get_back_kb("admin_auction_main")
    )
    await state.set_state(AdminAuctionStates.creating_auction_description)


@router.message(AdminAuctionStates.creating_auction_description)
async def process_auction_description(message: Message, state: FSMContext):
    """Process auction description input."""
    if not await is_admin(message.from_user.id, session):
        return
    
    description = message.text.strip()
    await state.update_data(description=description)
    
    await message.answer(
        f"✅ Descripción guardada.\n\n🎁 Ahora describe el premio de la subasta:",
        reply_markup=get_back_kb("admin_auction_main")
    )
    await state.set_state(AdminAuctionStates.creating_auction_prize)


@router.message(AdminAuctionStates.creating_auction_prize)
async def process_auction_prize(message: Message, state: FSMContext):
    """Process auction prize input."""
    if not await is_admin(message.from_user.id, session):
        return
    
    prize = message.text.strip()
    if len(prize) < 5:
        await send_temporary_reply(message, "❌ La descripción del premio debe ser más detallada.")
        return
    
    await state.update_data(prize_description=prize)
    await message.answer(
        f"🎁 Premio: **{prize}**\n\n💰 Ingresa el precio inicial de la subasta (en puntos):",
        reply_markup=get_back_kb("admin_auction_main")
    )
    await state.set_state(AdminAuctionStates.creating_auction_initial_price)


@router.message(AdminAuctionStates.creating_auction_initial_price)
async def process_auction_initial_price(message: Message, state: FSMContext):
    """Process auction initial price input."""
    if not await is_admin(message.from_user.id, session):
        return
    
    try:
        initial_price = int(message.text.strip())
        if initial_price < 1:
            raise ValueError("Price must be positive")
    except ValueError:
        await send_temporary_reply(message, "❌ Ingresa un número válido mayor a 0.")
        return
    
    await state.update_data(initial_price=initial_price)
    await message.answer(
        f"💰 Precio inicial: **{initial_price} puntos**\n\n⏰ Selecciona la duración de la subasta:",
        reply_markup=get_auction_duration_kb()
    )
    await state.set_state(AdminAuctionStates.creating_auction_duration)


@router.callback_query(AdminAuctionStates.creating_auction_duration, F.data.startswith("auction_duration_"))
async def process_auction_duration(callback: CallbackQuery, state: FSMContext):
    """Process auction duration selection."""
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer()
    
    duration_hours = int(callback.data.split("_")[-1])
    await state.update_data(duration_hours=duration_hours)
    
    # Show confirmation with all data
    data = await state.get_data()
    
    confirmation_text = (
        f"📋 **Resumen de la Subasta**\n\n"
        f"📝 **Nombre:** {data['name']}\n"
        f"📄 **Descripción:** {data['description']}\n"
        f"🎁 **Premio:** {data['prize_description']}\n"
        f"💰 **Precio inicial:** {data['initial_price']} puntos\n"
        f"⏰ **Duración:** {duration_hours} horas\n\n"
        f"¿Confirmas la creación de esta subasta?"
    )
    
    await callback.message.edit_text(
        confirmation_text,
        reply_markup=get_auction_confirmation_kb(data)
    )
    await state.set_state(AdminAuctionStates.confirming_auction_creation)
    await callback.answer()


@router.callback_query(AdminAuctionStates.confirming_auction_creation, F.data == "confirm_create_auction")
async def confirm_create_auction(callback: CallbackQuery, state: FSMContext, session: AsyncSession, bot: Bot):
    """Confirm and create the auction."""
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer()
    
    data = await state.get_data()
    auction_service = AuctionService(session)
    
    try:
        auction = await auction_service.create_auction(
            name=data['name'],
            description=data['description'],
            prize_description=data['prize_description'],
            initial_price=data['initial_price'],
            duration_hours=data['duration_hours'],
            created_by=callback.from_user.id
        )
        
        # Auto-start the auction
        await auction_service.start_auction(auction.id)
        
        success_text = (
            f"✅ **Subasta creada y iniciada**\n\n"
            f"🆔 ID: {auction.id}\n"
            f"📝 Nombre: {auction.name}\n"
            f"⏰ Finaliza: {auction.end_time.strftime('%d/%m/%Y %H:%M')}\n\n"
            f"La subasta ya está disponible para los usuarios."
        )
        
        await callback.message.edit_text(
            success_text,
            reply_markup=get_admin_auction_main_kb()
        )
        
        logger.info(f"Admin {callback.from_user.id} created auction: {auction.name}")
        
    except Exception as e:
        logger.error(f"Error creating auction: {e}")
        await callback.message.edit_text(
            f"❌ Error al crear la subasta: {str(e)}",
            reply_markup=get_admin_auction_main_kb()
        )
    
    await state.clear()
    await callback.answer()


@router.callback_query(F.data == "admin_list_active_auctions")
async def list_active_auctions(callback: CallbackQuery, session: AsyncSession):
    """List all active auctions."""
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer()
    
    auction_service = AuctionService(session)
    auctions = await auction_service.get_active_auctions()
    
    if not auctions:
        await callback.message.edit_text(
            "📋 **Subastas Activas**\n\nNo hay subastas activas en este momento.",
            reply_markup=get_back_kb("admin_auction_main")
        )
    else:
        text_lines = ["🔥 **Subastas Activas**\n"]
        for auction in auctions:
            time_remaining = format_time_remaining(auction.end_time)
            highest_bid = auction.current_highest_bid or auction.initial_price
            text_lines.append(
                f"• **{auction.name}**\n"
                f"  💰 Puja actual: {highest_bid} pts\n"
                f"  ⏰ Tiempo restante: {time_remaining}\n"
            )
        
        await callback.message.edit_text(
            "\n".join(text_lines),
            reply_markup=get_auction_list_kb(auctions, "manage")
        )
    
    await callback.answer()


@router.callback_query(F.data == "admin_list_pending_auctions")
async def list_pending_auctions(callback: CallbackQuery, session: AsyncSession):
    """List all pending auctions."""
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer()
    
    auction_service = AuctionService(session)
    auctions = await auction_service.get_pending_auctions()
    
    if not auctions:
        await callback.message.edit_text(
            "⏳ **Subastas Pendientes**\n\nNo hay subastas pendientes.",
            reply_markup=get_back_kb("admin_auction_main")
        )
    else:
        text_lines = ["⏳ **Subastas Pendientes**\n"]
        for auction in auctions:
            text_lines.append(
                f"• **{auction.name}**\n"
                f"  💰 Precio inicial: {auction.initial_price} pts\n"
                f"  📅 Creada: {auction.created_at.strftime('%d/%m/%Y %H:%M')}\n"
            )
        
        await callback.message.edit_text(
            "\n".join(text_lines),
            reply_markup=get_auction_list_kb(auctions, "manage")
        )
    
    await callback.answer()


@router.callback_query(F.data.startswith("manage_auction_"))
async def manage_auction(callback: CallbackQuery, session: AsyncSession):
    """Manage individual auction."""
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer()
    
    auction_id = int(callback.data.split("_")[-1])
    auction_service = AuctionService(session)
    
    auction_details = await auction_service.get_auction_details(auction_id, callback.from_user.id)
    if not auction_details:
        await callback.answer("❌ Subasta no encontrada", show_alert=True)
        return
    
    auction = auction_details['auction']
    
    details_text = (
        f"🏛️ **Gestión de Subasta**\n\n"
        f"📝 **Nombre:** {auction.name}\n"
        f"📄 **Descripción:** {auction.description}\n"
        f"🎁 **Premio:** {auction.prize_description}\n"
        f"💰 **Precio inicial:** {auction.initial_price} pts\n"
        f"🔥 **Puja actual:** {auction.current_highest_bid or 0} pts\n"
        f"👥 **Participantes:** {auction_details['participant_count']}\n"
        f"📊 **Estado:** {auction.status.value.title()}\n"
    )
    
    if auction.status.value == 'active':
        details_text += f"⏰ **Tiempo restante:** {auction_details['time_remaining']}\n"
    
    if auction.highest_bidder_id:
        details_text += f"🏆 **Pujador líder:** {auction_details['highest_bidder_display']}\n"
    
    await callback.message.edit_text(
        details_text,
        reply_markup=get_auction_action_kb(auction_id, auction.status.value)
    )
    await callback.answer()


@router.callback_query(F.data.startswith("end_auction_"))
async def confirm_end_auction(callback: CallbackQuery, session: AsyncSession):
    """Confirm ending an auction."""
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer()
    
    auction_id = int(callback.data.split("_")[-1])
    auction = await session.get(Auction, auction_id)
    
    if not auction:
        await callback.answer("❌ Subasta no encontrada", show_alert=True)
        return
    
    await callback.message.edit_text(
        f"⚠️ **Confirmar Finalización**\n\n"
        f"¿Estás seguro de que quieres finalizar la subasta **{auction.name}**?\n\n"
        f"Esta acción no se puede deshacer.",
        reply_markup=get_auction_confirm_action_kb("end", auction_id)
    )
    await callback.answer()


@router.callback_query(F.data.startswith("confirm_end_auction_"))
async def end_auction(callback: CallbackQuery, session: AsyncSession, bot: Bot):
    """End an auction."""
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer()
    
    auction_id = int(callback.data.split("_")[-1])
    auction_service = AuctionService(session)
    
    ended_auction = await auction_service.end_auction(auction_id, bot)
    
    if ended_auction:
        winner_text = "Sin ganador"
        if ended_auction.winner_id:
            winner = await session.get(User, ended_auction.winner_id)
            winner_text = anonymize_username(winner, callback.from_user.id)
        
        await callback.message.edit_text(
            f"✅ **Subasta Finalizada**\n\n"
            f"📝 **Subasta:** {ended_auction.name}\n"
            f"🏆 **Ganador:** {winner_text}\n"
            f"💰 **Puja ganadora:** {ended_auction.current_highest_bid} pts\n\n"
            f"Se han enviado las notificaciones correspondientes.",
            reply_markup=get_admin_auction_main_kb()
        )
        
        logger.info(f"Admin {callback.from_user.id} ended auction {auction_id}")
    else:
        await callback.message.edit_text(
            "❌ No se pudo finalizar la subasta.",
            reply_markup=get_admin_auction_main_kb()
        )
    
    await callback.answer()


@router.callback_query(F.data.startswith("cancel_auction_"))
async def confirm_cancel_auction(callback: CallbackQuery, session: AsyncSession):
    """Confirm cancelling an auction."""
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer()
    
    auction_id = int(callback.data.split("_")[-1])
    auction = await session.get(Auction, auction_id)
    
    if not auction:
        await callback.answer("❌ Subasta no encontrada", show_alert=True)
        return
    
    await callback.message.edit_text(
        f"⚠️ **Confirmar Cancelación**\n\n"
        f"¿Estás seguro de que quieres cancelar la subasta **{auction.name}**?\n\n"
        f"Esta acción no se puede deshacer y se notificará a todos los participantes.",
        reply_markup=get_auction_confirm_action_kb("cancel", auction_id)
    )
    await callback.answer()


@router.callback_query(F.data.startswith("confirm_cancel_auction_"))
async def cancel_auction(callback: CallbackQuery, session: AsyncSession, bot: Bot):
    """Cancel an auction."""
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer()
    
    auction_id = int(callback.data.split("_")[-1])
    auction_service = AuctionService(session)
    
    success = await auction_service.cancel_auction(auction_id, bot)
    
    if success:
        await callback.message.edit_text(
            f"✅ **Subasta Cancelada**\n\n"
            f"La subasta ha sido cancelada exitosamente.\n"
            f"Se han enviado las notificaciones a todos los participantes.",
            reply_markup=get_admin_auction_main_kb()
        )
        
        logger.info(f"Admin {callback.from_user.id} cancelled auction {auction_id}")
    else:
        await callback.message.edit_text(
            "❌ No se pudo cancelar la subasta.",
            reply_markup=get_admin_auction_main_kb()
        )
    
    await callback.answer()


@router.callback_query(F.data == "admin_auction_stats")
async def auction_statistics(callback: CallbackQuery, session: AsyncSession):
    """Show auction statistics."""
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer()
    
    auction_service = AuctionService(session)
    
    # Get statistics
    from sqlalchemy import func
    from database.models import Auction, Bid
    
    # Total auctions
    total_stmt = select(func.count()).select_from(Auction)
    total_result = await session.execute(total_stmt)
    total_auctions = total_result.scalar() or 0
    
    # Active auctions
    active_auctions = await auction_service.get_active_auctions()
    active_count = len(active_auctions)
    
    # Pending auctions
    pending_auctions = await auction_service.get_pending_auctions()
    pending_count = len(pending_auctions)
    
    # Total bids
    bids_stmt = select(func.count()).select_from(Bid)
    bids_result = await session.execute(bids_stmt)
    total_bids = bids_result.scalar() or 0
    
    # Total points in circulation
    points_stmt = select(func.sum(Bid.amount)).select_from(Bid)
    points_result = await session.execute(points_stmt)
    total_points_bid = points_result.scalar() or 0
    
    stats_text = (
        f"📊 **Estadísticas de Subastas**\n\n"
        f"🏛️ **Subastas totales:** {total_auctions}\n"
        f"🔥 **Activas:** {active_count}\n"
        f"⏳ **Pendientes:** {pending_count}\n"
        f"🏁 **Finalizadas:** {total_auctions - active_count - pending_count}\n\n"
        f"💰 **Pujas totales:** {total_bids}\n"
        f"🎯 **Puntos en juego:** {format_points(total_points_bid)}\n"
    )
    
    await callback.message.edit_text(
        stats_text,
        reply_markup=get_back_kb("admin_auction_main")
    )
    await callback.answer()
