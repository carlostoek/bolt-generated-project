from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timedelta
from typing import List, Optional, Tuple

from aiogram import Bot
from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import (
    Auction, 
    Bid, 
    AuctionParticipant, 
    User, 
    AuctionStatus
)
from utils.text_utils import anonymize_username, format_points, format_time_remaining
from services.point_service import PointService

logger = logging.getLogger(__name__)


class AuctionService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.point_service = PointService(session)

    async def create_auction(
        self,
        name: str,
        description: str,
        prize_description: str,
        initial_price: int,
        duration_hours: int,
        created_by: int,
        min_bid_increment: int = 10,
        max_participants: Optional[int] = None,
        auto_extend_minutes: int = 5
    ) -> Auction:
        """Create a new auction."""
        start_time = datetime.utcnow()
        end_time = start_time + timedelta(hours=duration_hours)
        
        auction = Auction(
            name=name,
            description=description,
            prize_description=prize_description,
            initial_price=initial_price,
            current_highest_bid=0,
            status=AuctionStatus.PENDING,
            start_time=start_time,
            end_time=end_time,
            created_by=created_by,
            min_bid_increment=min_bid_increment,
            max_participants=max_participants,
            auto_extend_minutes=auto_extend_minutes
        )
        
        self.session.add(auction)
        await self.session.commit()
        await self.session.refresh(auction)
        
        logger.info(f"Auction '{name}' created by user {created_by}")
        return auction

    async def start_auction(self, auction_id: int) -> bool:
        """Start a pending auction."""
        auction = await self.session.get(Auction, auction_id)
        if not auction or auction.status != AuctionStatus.PENDING:
            return False
        
        auction.status = AuctionStatus.ACTIVE
        auction.start_time = datetime.utcnow()
        await self.session.commit()
        
        logger.info(f"Auction {auction_id} started")
        return True

    async def place_bid(
        self, 
        auction_id: int, 
        user_id: int, 
        amount: int,
        bot: Optional[Bot] = None
    ) -> Tuple[bool, str]:
        """
        Place a bid in an auction.
        
        Returns:
            Tuple[bool, str]: (success, message)
        """
        auction = await self.session.get(Auction, auction_id)
        if not auction:
            return False, "Subasta no encontrada"
        
        if auction.status != AuctionStatus.ACTIVE:
            return False, "La subasta no está activa"
        
        if datetime.utcnow() > auction.end_time:
            return False, "La subasta ha finalizado"
        
        # Check if user has enough points
        user = await self.session.get(User, user_id)
        if not user or user.points < amount:
            return False, f"No tienes suficientes puntos. Necesitas {amount}, tienes {format_points(user.points)}"
        
        # Validate bid amount
        min_bid = max(auction.initial_price, auction.current_highest_bid + auction.min_bid_increment)
        if amount < min_bid:
            return False, f"La puja mínima es {min_bid} puntos"
        
        # Check if user is already the highest bidder
        if auction.highest_bidder_id == user_id:
            return False, "Ya eres el pujador más alto"
        
        # Check participant limit
        if auction.max_participants:
            participant_count = await self._get_participant_count(auction_id)
            if participant_count >= auction.max_participants:
                # Check if user is already a participant
                is_participant = await self._is_participant(auction_id, user_id)
                if not is_participant:
                    return False, f"La subasta está limitada a {auction.max_participants} participantes"
        
        # Create the bid
        bid = Bid(
            auction_id=auction_id,
            user_id=user_id,
            amount=amount,
            is_winning=True
        )
        
        # Update previous winning bid
        if auction.highest_bidder_id:
            await self._update_previous_winning_bid(auction_id, auction.highest_bidder_id)
        
        # Update auction
        auction.current_highest_bid = amount
        auction.highest_bidder_id = user_id
        
        # Auto-extend if bid is placed in the last few minutes
        time_remaining = auction.end_time - datetime.utcnow()
        if time_remaining.total_seconds() < (auction.auto_extend_minutes * 60):
            auction.end_time = datetime.utcnow() + timedelta(minutes=auction.auto_extend_minutes)
            logger.info(f"Auction {auction_id} auto-extended due to late bid")
        
        self.session.add(bid)
        
        # Add user as participant if not already
        await self._ensure_participant(auction_id, user_id)
        
        await self.session.commit()
        
        # Send notifications to other participants
        if bot:
            await self._notify_participants(auction, user_id, amount, bot)
        
        logger.info(f"User {user_id} placed bid of {amount} points in auction {auction_id}")
        return True, f"¡Puja de {amount} puntos realizada con éxito!"

    async def end_auction(self, auction_id: int, bot: Optional[Bot] = None) -> Optional[Auction]:
        """End an auction and determine the winner."""
        auction = await self.session.get(Auction, auction_id)
        if not auction or auction.status != AuctionStatus.ACTIVE:
            return None
        
        auction.status = AuctionStatus.ENDED
        auction.ended_at = datetime.utcnow()
        
        if auction.highest_bidder_id and auction.current_highest_bid > 0:
            auction.winner_id = auction.highest_bidder_id
            
            # Deduct points from winner
            await self.point_service.deduct_points(auction.winner_id, auction.current_highest_bid)
            
            # Notify winner
            if bot:
                try:
                    await bot.send_message(
                        auction.winner_id,
                        f"🎉 ¡Felicidades! Has ganado la subasta '{auction.name}'\n"
                        f"🏆 Premio: {auction.prize_description}\n"
                        f"💰 Puja ganadora: {auction.current_highest_bid} puntos\n\n"
                        f"Te contactaremos pronto para entregarte tu premio."
                    )
                except Exception as e:
                    logger.error(f"Failed to notify auction winner {auction.winner_id}: {e}")
                
                # Notify all participants about the result
                await self._notify_auction_ended(auction, bot)
        
        await self.session.commit()
        await self.session.refresh(auction)
        
        logger.info(f"Auction {auction_id} ended. Winner: {auction.winner_id}")
        return auction

    async def cancel_auction(self, auction_id: int, bot: Optional[Bot] = None) -> bool:
        """Cancel an auction."""
        auction = await self.session.get(Auction, auction_id)
        if not auction or auction.status == AuctionStatus.ENDED:
            return False
        
        auction.status = AuctionStatus.CANCELLED
        auction.ended_at = datetime.utcnow()
        
        # Notify participants
        if bot:
            await self._notify_auction_cancelled(auction, bot)
        
        await self.session.commit()
        
        logger.info(f"Auction {auction_id} cancelled")
        return True

    async def get_active_auctions(self) -> List[Auction]:
        """Get all active auctions."""
        stmt = select(Auction).where(
            Auction.status == AuctionStatus.ACTIVE,
            Auction.end_time > datetime.utcnow()
        ).order_by(Auction.end_time)
        
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_pending_auctions(self) -> List[Auction]:
        """Get all pending auctions."""
        stmt = select(Auction).where(
            Auction.status == AuctionStatus.PENDING
        ).order_by(Auction.start_time)
        
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_auction_details(self, auction_id: int, viewer_user_id: int) -> Optional[dict]:
        """Get detailed auction information with anonymized participant data."""
        auction = await self.session.get(Auction, auction_id)
        if not auction:
            return None
        
        # Get highest bidder info (anonymized)
        highest_bidder = None
        if auction.highest_bidder_id:
            highest_bidder = await self.session.get(User, auction.highest_bidder_id)
        
        # Get recent bids (last 5)
        stmt = select(Bid).where(Bid.auction_id == auction_id).order_by(Bid.timestamp.desc()).limit(5)
        result = await self.session.execute(stmt)
        recent_bids = result.scalars().all()
        
        # Get participant count
        participant_count = await self._get_participant_count(auction_id)
        
        # Check if viewer is participating
        is_participating = await self._is_participant(auction_id, viewer_user_id)
        
        # Get viewer's highest bid
        viewer_highest_bid = await self._get_user_highest_bid(auction_id, viewer_user_id)
        
        return {
            'auction': auction,
            'highest_bidder_display': anonymize_username(highest_bidder, viewer_user_id) if highest_bidder else None,
            'recent_bids': [
                {
                    'amount': bid.amount,
                    'timestamp': bid.timestamp,
                    'bidder_display': anonymize_username(
                        await self.session.get(User, bid.user_id), 
                        viewer_user_id
                    )
                }
                for bid in recent_bids
            ],
            'participant_count': participant_count,
            'is_participating': is_participating,
            'viewer_highest_bid': viewer_highest_bid,
            'time_remaining': format_time_remaining(auction.end_time),
            'min_next_bid': max(auction.initial_price, auction.current_highest_bid + auction.min_bid_increment)
        }

    async def get_user_auctions(self, user_id: int, include_ended: bool = False) -> List[Auction]:
        """Get auctions where user has participated."""
        stmt = select(Auction).join(AuctionParticipant).where(
            AuctionParticipant.user_id == user_id
        )
        
        if not include_ended:
            stmt = stmt.where(Auction.status.in_([AuctionStatus.PENDING, AuctionStatus.ACTIVE]))
        
        stmt = stmt.order_by(Auction.created_at.desc())
        
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def check_expired_auctions(self, bot: Optional[Bot] = None) -> List[Auction]:
        """Check for expired auctions and end them automatically."""
        stmt = select(Auction).where(
            Auction.status == AuctionStatus.ACTIVE,
            Auction.end_time <= datetime.utcnow()
        )
        
        result = await self.session.execute(stmt)
        expired_auctions = result.scalars().all()
        
        ended_auctions = []
        for auction in expired_auctions:
            ended_auction = await self.end_auction(auction.id, bot)
            if ended_auction:
                ended_auctions.append(ended_auction)
        
        return ended_auctions

    # Private helper methods
    async def _get_participant_count(self, auction_id: int) -> int:
        """Get number of participants in an auction."""
        stmt = select(func.count()).select_from(AuctionParticipant).where(
            AuctionParticipant.auction_id == auction_id
        )
        result = await self.session.execute(stmt)
        return result.scalar() or 0

    async def _is_participant(self, auction_id: int, user_id: int) -> bool:
        """Check if user is participating in auction."""
        stmt = select(AuctionParticipant).where(
            AuctionParticipant.auction_id == auction_id,
            AuctionParticipant.user_id == user_id
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none() is not None

    async def _ensure_participant(self, auction_id: int, user_id: int):
        """Ensure user is registered as participant."""
        if not await self._is_participant(auction_id, user_id):
            participant = AuctionParticipant(
                auction_id=auction_id,
                user_id=user_id
            )
            self.session.add(participant)

    async def _get_user_highest_bid(self, auction_id: int, user_id: int) -> Optional[int]:
        """Get user's highest bid in an auction."""
        stmt = select(func.max(Bid.amount)).where(
            Bid.auction_id == auction_id,
            Bid.user_id == user_id
        )
        result = await self.session.execute(stmt)
        return result.scalar()

    async def _update_previous_winning_bid(self, auction_id: int, previous_bidder_id: int):
        """Mark previous winning bid as no longer winning."""
        stmt = select(Bid).where(
            Bid.auction_id == auction_id,
            Bid.user_id == previous_bidder_id,
            Bid.is_winning == True
        )
        result = await self.session.execute(stmt)
        previous_bid = result.scalar_one_or_none()
        
        if previous_bid:
            previous_bid.is_winning = False

    async def _notify_participants(self, auction: Auction, new_bidder_id: int, amount: int, bot: Bot):
        """Notify all participants about a new bid."""
        stmt = select(AuctionParticipant).where(
            AuctionParticipant.auction_id == auction.id,
            AuctionParticipant.user_id != new_bidder_id,
            AuctionParticipant.notifications_enabled == True
        )
        result = await self.session.execute(stmt)
        participants = result.scalars().all()
        
        new_bidder = await self.session.get(User, new_bidder_id)
        
        for participant in participants:
            try:
                bidder_display = anonymize_username(new_bidder, participant.user_id)
                time_remaining = format_time_remaining(auction.end_time)
                
                message = (
                    f"🔔 Nueva puja en '{auction.name}'\n"
                    f"💰 Puja actual: {amount} puntos\n"
                    f"👤 Pujador: {bidder_display}\n"
                    f"⏰ Tiempo restante: {time_remaining}\n\n"
                    f"¡Haz tu puja para no perder la oportunidad!"
                )
                
                await bot.send_message(participant.user_id, message)
                participant.last_notified_at = datetime.utcnow()
                
            except Exception as e:
                logger.error(f"Failed to notify participant {participant.user_id}: {e}")
        
        await self.session.commit()

    async def _notify_auction_ended(self, auction: Auction, bot: Bot):
        """Notify all participants that auction has ended."""
        stmt = select(AuctionParticipant).where(
            AuctionParticipant.auction_id == auction.id
        )
        result = await self.session.execute(stmt)
        participants = result.scalars().all()
        
        winner = None
        if auction.winner_id:
            winner = await self.session.get(User, auction.winner_id)
        
        for participant in participants:
            try:
                if participant.user_id == auction.winner_id:
                    continue  # Winner already notified separately
                
                winner_display = anonymize_username(winner, participant.user_id) if winner else "Nadie"
                
                message = (
                    f"🏁 Subasta finalizada: '{auction.name}'\n"
                    f"🏆 Ganador: {winner_display}\n"
                    f"💰 Puja ganadora: {auction.current_highest_bid} puntos\n"
                    f"🎁 Premio: {auction.prize_description}"
                )
                
                await bot.send_message(participant.user_id, message)
                
            except Exception as e:
                logger.error(f"Failed to notify participant {participant.user_id} about auction end: {e}")

    async def _notify_auction_cancelled(self, auction: Auction, bot: Bot):
        """Notify all participants that auction was cancelled."""
        stmt = select(AuctionParticipant).where(
            AuctionParticipant.auction_id == auction.id
        )
        result = await self.session.execute(stmt)
        participants = result.scalars().all()
        
        for participant in participants:
            try:
                message = (
                    f"❌ Subasta cancelada: '{auction.name}'\n"
                    f"La subasta ha sido cancelada por el administrador.\n"
                    f"Disculpa las molestias."
                )
                
                await bot.send_message(participant.user_id, message)
                
            except Exception as e:
                logger.error(f"Failed to notify participant {participant.user_id} about cancellation: {e}")
