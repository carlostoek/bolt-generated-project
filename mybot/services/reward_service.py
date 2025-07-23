from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from database.models import Reward, User, UserReward
from utils.text_utils import sanitize_text
from utils.messages import BOT_MESSAGES
import logging

logger = logging.getLogger(__name__)


class RewardService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_active_rewards(self) -> list[Reward]:
        stmt = select(Reward).where(Reward.is_active == True)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_available_rewards(self, user_points: int) -> list[Reward]:
        stmt = (
            select(Reward)
            .where(Reward.is_active == True, Reward.required_points <= user_points)
            .order_by(Reward.required_points)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_claimed_reward_ids(self, user_id: int) -> list[int]:
        stmt = select(UserReward.reward_id).where(UserReward.user_id == user_id)
        result = await self.session.execute(stmt)
        return [row[0] for row in result.all()]

    async def get_reward_by_id(self, reward_id: int) -> Reward | None:
        return await self.session.get(Reward, reward_id)

    async def list_rewards(self) -> list[Reward]:
        """Return all rewards regardless of status."""
        result = await self.session.execute(select(Reward))
        return result.scalars().all()

    async def claim_reward(self, user_id: int, reward_id: int) -> tuple[bool, str]:
        """Claim a reward once the user has enough points."""
        user = await self.session.get(User, user_id)
        reward = await self.session.get(Reward, reward_id)
        if not user:
            return False, "Usuario no encontrado."
        if not reward or not reward.is_active:
            return False, "Recompensa no disponible."
        if user.points < reward.required_points:
            return (
                False,
                BOT_MESSAGES.get(
                    "reward_not_enough_points",
                    "No tienes suficientes puntos para esta recompensa.",
                ).format(
                    required_points=reward.required_points, user_points=int(user.points)
                ),
            )
        stmt = select(UserReward).where(
            UserReward.user_id == user_id, UserReward.reward_id == reward_id
        )
        result = await self.session.execute(stmt)
        if result.scalar_one_or_none():
            return False, BOT_MESSAGES.get("reward_already_claimed", "Ya reclamado")
        self.session.add(UserReward(user_id=user_id, reward_id=reward_id))
        await self.session.commit()
        return True, BOT_MESSAGES.get("reward_claim_success", "Recompensa reclamada")

    async def create_reward(
        self,
        title: str,
        required_points: int,
        description: str | None = None,
        reward_type: str | None = None,
    ) -> Reward:
        new_reward = Reward(
            title=sanitize_text(title),
            description=sanitize_text(description) if description else None,
            required_points=required_points,
            reward_type=reward_type,
        )
        self.session.add(new_reward)
        await self.session.commit()
        await self.session.refresh(new_reward)
        logger.info(f"New reward '{title}' created by admin.")
        return new_reward

    async def toggle_reward_status(self, reward_id: int, status: bool) -> bool:
        reward = await self.session.get(Reward, reward_id)
        if reward:
            reward.is_active = status
            await self.session.commit()
            logger.info(f"Reward '{reward.title}' status set to {status}.")
            return True
        logger.warning(f"Failed to toggle status for reward {reward_id}. Not found.")
        return False

    async def update_reward(
        self,
        reward_id: int,
        *,
        title: str | None = None,
        required_points: int | None = None,
        description: str | None = None,
        reward_type: str | None = None,
    ) -> bool:
        reward = await self.session.get(Reward, reward_id)
        if not reward:
            return False
        if title is not None:
            reward.title = sanitize_text(title)
        if required_points is not None:
            reward.required_points = required_points
        if description is not None:
            reward.description = sanitize_text(description)
        if reward_type is not None:
            reward.reward_type = reward_type
        await self.session.commit()
        return True

    async def delete_reward(self, reward_id: int) -> bool:
        reward = await self.session.get(Reward, reward_id)
        if not reward:
            return False
        await self.session.delete(reward)
        await self.session.commit()
        return True
