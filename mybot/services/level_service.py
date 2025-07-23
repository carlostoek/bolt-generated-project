from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from aiogram import Bot

from database.models import User, Level, LorePiece, UserLorePiece
from utils.messages import BOT_MESSAGES
import logging

logger = logging.getLogger(__name__)

DEFAULT_LEVELS = [
    # level_id, name, min_points, reward
    (1, "Novato", 0, ""),
    (2, "Aprendiz", 500, ""),
    (3, "Aventurero", 1000, ""),
    (4, "Explorador", 1500, ""),
    (5, "Héroe", 2000, "Un pequeño obsequio"),
    (6, "Guerrero", 2500, "Acceso a contenido exclusivo"),
    (7, "Veterano", 3000, ""),
    (8, "Maestro", 3500, ""),
    (9, "Leyenda", 4000, ""),
    (10, "Campeón", 4500, "Gran reconocimiento"),
    (11, "Mítico", 5500, ""),
    (12, "Épico", 6500, ""),
    (13, "Supremo", 7500, ""),
    (14, "Legendario", 8500, ""),
    (15, "Divino", 9500, "Recompensa especial"),
    (16, "Inmortal", 10500, ""),
    (17, "Titán", 11500, ""),
    (18, "Olimpo", 12500, ""),
    (19, "Estelar", 13500, ""),
    (20, "Cosmos", 14500, "Recompensa épica"),
]

# Tabla de niveles usada para el cálculo rápido sin acceso a base de datos
LEVELS = [
    (1, 0),
    (2, 100),
    (3, 250),
    (4, 500),
    (5, 800),
    (6, 1200),
    (7, 1800),
    (8, 2500),
    (9, 3500),
    (10, 5000),
]

class LevelService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def _init_levels(self) -> None:
        result = await self.session.execute(select(Level))
        if result.scalars().first():
            return
        for level_id, name, min_points, reward in DEFAULT_LEVELS:
            self.session.add(Level(level_id=level_id, name=name, min_points=min_points, reward=reward))
        await self.session.commit()

    async def _get_levels(self) -> list[Level]:
        await self._init_levels()
        result = await self.session.execute(select(Level).order_by(Level.min_points))
        return result.scalars().all()

    async def list_levels(self) -> list[Level]:
        """Return all levels ordered by their number."""
        result = await self.session.execute(select(Level).order_by(Level.level_id))
        return result.scalars().all()

    async def create_level(
        self,
        level_number: int,
        name: str,
        required_points: int,
        reward: str | None = None,
    ) -> Level:
        new_level = Level(
            level_id=level_number,
            name=name,
            min_points=required_points,
            reward=reward,
        )
        self.session.add(new_level)
        await self.session.commit()
        await self.session.refresh(new_level)
        return new_level

    async def update_level(
        self,
        level_id: int,
        *,
        new_level_number: int | None = None,
        name: str | None = None,
        required_points: int | None = None,
        reward: str | None = None,
    ) -> bool:
        level = await self.session.get(Level, level_id)
        if not level:
            return False
        if new_level_number is not None:
            level.level_id = new_level_number
        if name is not None:
            level.name = name
        if required_points is not None:
            level.min_points = required_points
        if reward is not None:
            level.reward = reward
        await self.session.commit()
        return True

    async def delete_level(self, level_id: int) -> bool:
        level = await self.session.get(Level, level_id)
        if not level:
            return False
        await self.session.delete(level)
        await self.session.commit()
        return True

    async def get_level_threshold(self, level_id: int) -> int:
        levels = await self._get_levels()
        for lvl in levels:
            if lvl.level_id == level_id:
                return lvl.min_points
        return float("inf")

    async def get_level_for_points(self, points: float) -> Level:
        levels = await self._get_levels()
        current = levels[0]
        for lvl in levels:
            if points >= lvl.min_points:
                current = lvl
            else:
                break
        return current

    async def check_for_level_up(self, user: User, *, bot: Bot | None = None) -> bool:
        new_level = await self.get_level_for_points(user.points)
        if new_level.level_id != user.level:
            user.level = new_level.level_id
            await self.session.commit()
            await self.session.refresh(user)
            if bot:
                msg = BOT_MESSAGES["level_up_notification"].format(
                    level=new_level.level_id,
                    level_name=new_level.name,
                    reward=new_level.reward or "",
                )
                await bot.send_message(user.id, msg)
                if new_level.level_id in {5, 10, 15, 20}:
                    special_msg = BOT_MESSAGES["special_level_reward"].format(
                        level=new_level.level_id,
                        reward=new_level.reward or "",
                    )
                    await bot.send_message(user.id, special_msg)

            # Desbloquear pistas de lore asociadas al nivel alcanzado
            unlock_code = getattr(new_level, "unlocks_lore_piece_code", None)
            if unlock_code:
                lore_stmt = select(LorePiece).where(LorePiece.code_name == unlock_code)
                lore_piece = (await self.session.execute(lore_stmt)).scalar_one_or_none()
                if lore_piece:
                    check_stmt = select(UserLorePiece).where(
                        UserLorePiece.user_id == user.id,
                        UserLorePiece.lore_piece_id == lore_piece.id,
                    )
                    exists = (await self.session.execute(check_stmt)).scalar_one_or_none()
                    if not exists:
                        self.session.add(UserLorePiece(user_id=user.id, lore_piece_id=lore_piece.id))
                        await self.session.commit()
                        if bot:
                            await bot.send_message(user.id, f"Has desbloqueado una nueva pista: {lore_piece.title}")
                        logger.info(
                            f"User {user.id} unlocked lore piece {unlock_code} via level {new_level.level_id}"
                        )
            return True
        return False


def get_user_level(points: int) -> int:
    """Calculate user level based on accumulated points."""
    current_level = LEVELS[0][0]
    for level, threshold in LEVELS:
        if points >= threshold:
            current_level = level
        else:
            break
    return current_level


def get_next_level_info(points: int) -> dict:
    """Return progress information towards the next level."""
    current_level = get_user_level(points)

    # Find thresholds for current and next levels
    current_threshold = 0
    next_threshold = None
    for level, threshold in LEVELS:
        if level == current_level:
            current_threshold = threshold
        elif level > current_level and next_threshold is None:
            next_threshold = threshold
            break

    if next_threshold is None:
        # At max level
        return {
            "current_level": current_level,
            "next_level": current_level,
            "points_needed": 0,
            "percentage_to_next": 1.0,
        }

    points_needed = max(0, next_threshold - points)
    total_range = next_threshold - current_threshold
    percentage = (points - current_threshold) / total_range if total_range else 1

    return {
        "current_level": current_level,
        "next_level": current_level + 1,
        "points_needed": points_needed,
        "percentage_to_next": min(max(percentage, 0), 1),
    }
