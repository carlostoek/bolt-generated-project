import datetime
from aiogram import Bot
from sqlalchemy.ext.asyncio import AsyncSession
from database.models import UserStats, MiniGamePlay, Mission, UserMissionEntry
from .point_service import PointService
from .mission_service import MissionService

class MiniGameService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.point_service = PointService(session)

    async def play_roulette(self, user_id: int, bot: Bot, *, cost: int = 5) -> int:
        """Play roulette. Returns points won."""
        progress = await self.session.get(UserStats, user_id)
        if not progress:
            progress = UserStats(user_id=user_id)
            self.session.add(progress)
            await self.session.commit()
        now = datetime.datetime.utcnow()
        free_available = not progress.last_roulette_at or (now - progress.last_roulette_at).total_seconds() >= 86400
        is_free = free_available
        if not free_available:
            await self.point_service.deduct_points(user_id, cost)
        progress.last_roulette_at = now
        score = bot.dice_emoji if hasattr(bot, "dice_emoji") else None
        dice_msg = await bot.send_dice(user_id)
        score = dice_msg.dice.value
        await self.point_service.add_points(user_id, score, bot=bot)
        play = MiniGamePlay(
            user_id=user_id,
            game_type="roulette",
            is_free=is_free,
            cost_points=0 if is_free else cost,
        )
        self.session.add(play)
        await self.session.commit()
        return score

    async def start_reaction_challenge(self, user_id: int, reactions: int, duration_minutes: int = 10, reward: int = 5, penalty: int = 2) -> Mission:
        ms = MissionService(self.session)
        mission_name = f"Reaction Challenge {user_id}"
        description = f"Reacciona {reactions} veces en {duration_minutes} minutos"
        mission = await ms.create_mission(
            mission_name,
            description,
            "reaction_challenge",
            reactions,
            reward,
            duration_days=0,
            requires_action=False,
            action_data={"duration_minutes": duration_minutes, "penalty_points": penalty},
        )
        entry = UserMissionEntry(user_id=user_id, mission_id=mission.id)
        self.session.add(entry)
        await self.session.commit()
        return mission

    async def record_reaction(self, user_id: int, bot: Bot):
        ms = MissionService(self.session)
        await ms.update_progress(user_id, "reaction_challenge", increment=1, bot=bot)
