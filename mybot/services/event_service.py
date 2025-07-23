from __future__ import annotations

import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from database.models import Event


class EventService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_event(self, name: str, description: str, multiplier: int) -> Event:
        event = Event(
            name=name,
            description=description,
            multiplier=multiplier,
            is_active=True,
            start_time=datetime.datetime.utcnow(),
        )
        self.session.add(event)
        await self.session.commit()
        await self.session.refresh(event)
        return event

    async def list_active_events(self) -> list[Event]:
        stmt = select(Event).where(Event.is_active == True)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def list_events(self) -> list[Event]:
        stmt = select(Event)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def end_event(self, event_id: int) -> Event | None:
        event = await self.session.get(Event, event_id)
        if event and event.is_active:
            event.is_active = False
            event.end_time = datetime.datetime.utcnow()
            await self.session.commit()
            await self.session.refresh(event)
        return event

    async def get_multiplier(self) -> int:
        events = await self.list_active_events()
        mult = 1
        for ev in events:
            try:
                mult *= int(ev.multiplier)
            except Exception:
                pass
        return mult
