from __future__ import annotations

from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from database.models import SubscriptionPlan
from utils.text_utils import sanitize_text


class SubscriptionPlanService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_plan(self, created_by: int, name: str, price: int, duration_days: int) -> SubscriptionPlan:
        plan = SubscriptionPlan(
            name=sanitize_text(name),
            price=price,
            duration_days=duration_days,
            created_by=created_by,
            status="available",
        )
        self.session.add(plan)
        await self.session.commit()
        await self.session.refresh(plan)
        return plan

    async def get_plan_by_id(self, plan_id: int) -> SubscriptionPlan | None:
        return await self.session.get(SubscriptionPlan, plan_id)

    async def list_plans(self) -> list[SubscriptionPlan]:
        result = await self.session.execute(select(SubscriptionPlan))
        return result.scalars().all()
