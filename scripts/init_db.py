import asyncio
import os
import sys

# Añadimos la raíz del proyecto al sys.path para permitir las importaciones
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.abspath(os.path.join(SCRIPT_DIR, os.pardir))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from database.setup import init_db, get_session
from services.achievement_service import AchievementService
from services.level_service import LevelService
from services.mission_service import MissionService
from sqlalchemy.future import select
from database.models import LorePiece, NarrativeFragment
from scripts.populate_narrative import populate_narrative_data

DEFAULT_MISSIONS = [
    {
        "name": "Daily Check-in",
        "description": "Registra tu actividad diaria con /checkin",
        "reward_points": 10,
        "mission_type": "login_streak",
        "target_value": 1,
        "duration_days": 0,
    },
    {
        "name": "Primer Mensaje",
        "description": "Envía tu primer mensaje en el chat",
        "reward_points": 5,
        "mission_type": "messages",
        "target_value": 1,
        "duration_days": 0,
    },
]

async def main() -> None:
    await init_db()
    Session = await get_session()
    async with Session() as session:
        await AchievementService(session).ensure_achievements_exist()
        level_service = LevelService(session)
        await level_service._init_levels()

        mission_service = MissionService(session)
        existing = await mission_service.get_active_missions()
        if not existing:
            for m in DEFAULT_MISSIONS:
                await mission_service.create_mission(
                    m["name"],
                    m["description"],
                    m["mission_type"],
                    m.get("target_value", 1),
                    m["reward_points"],
                    m.get("duration_days", 0),
                )

        # Ensure a test LorePiece exists for development/testing
        existing_pista = await session.execute(
            select(LorePiece).where(LorePiece.code_name == "TEST_P_1")
        )
        if not existing_pista.scalar_one_or_none():
            test_lore_piece = LorePiece(
                code_name="TEST_P_1",
                title="El Diario Olvidado",
                description="Una página arrancada del diario de Diana. Parece hablar de un encuentro en un viejo café.",
                content="¡No te olvides de la cafetería en la Calle del Tiempo Perdido! Algo mágico me sucedió allí...",
                content_type="text",
                category="memorias",
            )
            session.add(test_lore_piece)
            await session.commit()
            print("Pista de prueba 'TEST_P_1' añadida.")
        else:
            print("Pista de prueba 'TEST_P_1' ya existe.")

        # Populate narrative data
        existing_narrative = await session.execute(
            select(NarrativeFragment).where(NarrativeFragment.key == "start")
        )
        if not existing_narrative.scalar_one_or_none():
            await populate_narrative_data(session)

    print("Database initialised")

if __name__ == "__main__":
    asyncio.run(main())
