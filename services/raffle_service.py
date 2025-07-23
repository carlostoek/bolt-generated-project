from __future__ import annotations

import datetime
import random
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from database.models import Raffle, RaffleEntry


class RaffleService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_raffle(self, name: str, description: str, prize: str) -> Raffle:
        raffle = Raffle(
            name=name,
            description=description,
            prize=prize,
            is_active=True,
            created_at=datetime.datetime.utcnow(),
        )
        self.session.add(raffle)
        await self.session.commit()
        await self.session.refresh(raffle)
        return raffle

    async def add_entry(self, raffle_id: int, user_id: int) -> RaffleEntry:
        entry = RaffleEntry(raffle_id=raffle_id, user_id=user_id)
        self.session.add(entry)
        await self.session.commit()
        await self.session.refresh(entry)
        return entry

    async def list_active_raffles(self) -> list[Raffle]:
        stmt = select(Raffle).where(Raffle.is_active == True)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def list_raffles(self) -> list[Raffle]:
        stmt = select(Raffle)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def end_raffle(self, raffle_id: int) -> Raffle | None:
        raffle = await self.session.get(Raffle, raffle_id)
        if raffle and raffle.is_active:
            stmt = select(RaffleEntry).where(RaffleEntry.raffle_id == raffle_id)
            entries = (await self.session.execute(stmt)).scalars().all()
            if entries:
                winner = random.choice(entries)
                raffle.winner_id = winner.user_id
            raffle.is_active = False
            raffle.ended_at = datetime.datetime.utcnow()
            await self.session.commit()
            await self.session.refresh(raffle)
        return raffle

    async def list_entries(self, raffle_id: int) -> list[RaffleEntry]:
        stmt = select(RaffleEntry).where(RaffleEntry.raffle_id == raffle_id)
        result = await self.session.execute(stmt)
        return result.scalars().all()
