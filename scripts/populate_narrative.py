# scripts/populate_narrative.py
import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from mybot.database.setup import get_session, init_db
from mybot.database.narrative_models import StoryFragment, NarrativeChoice
from scripts.story_content import STORY_BOARD

async def populate_narrative_data(session: AsyncSession):
    """
    Populates the narrative tables from the STORY_BOARD structure.
    This function is idempotent: it updates existing fragments based on their key
    or creates them if they don't exist.
    """
    print("Syncing narrative storyboard with the database...")

    # Clear existing choices to avoid orphans
    await session.execute(NarrativeChoice.__table__.delete())
    await session.commit()

    # Process all fragments first
    for fragment_data in STORY_BOARD:
        key = fragment_data["key"]
        
        # Check if fragment exists
        result = await session.execute(select(StoryFragment).where(StoryFragment.key == key))
        fragment = result.scalar_one_or_none()

        if fragment:
            # Update existing fragment
            print(f"Updating fragment: {key}")
            fragment.text = fragment_data["text"]
            fragment.character = fragment_data.get("character", "Lucien")
            fragment.auto_next_fragment_key = fragment_data.get("auto_next_fragment_key")
            fragment.level = fragment_data.get("level", 1)
            fragment.min_besitos = fragment_data.get("min_besitos", 0)
            fragment.required_role = fragment_data.get("required_role")
            fragment.reward_besitos = fragment_data.get("reward_besitos", 0)
            fragment.unlocks_achievement_id = fragment_data.get("unlocks_achievement_id")
        else:
            # Create new fragment
            print(f"Creating fragment: {key}")
            fragment = StoryFragment(
                key=key,
                text=fragment_data["text"],
                character=fragment_data.get("character", "Lucien"),
                auto_next_fragment_key=fragment_data.get("auto_next_fragment_key"),
                level=fragment_data.get("level", 1),
                min_besitos=fragment_data.get("min_besitos", 0),
                required_role=fragment_data.get("required_role"),
                reward_besitos=fragment_data.get("reward_besitos", 0),
                unlocks_achievement_id=fragment_data.get("unlocks_achievement_id"),
            )
            session.add(fragment)
    
    # Commit fragments to ensure they all have IDs
    await session.commit()
    print("All fragments synced.")

    # Re-fetch all fragments to have access to their IDs
    result = await session.execute(select(StoryFragment))
    fragments_map = {f.key: f for f in result.scalars().all()}

    # Process all choices
    print("Populating narrative choices...")
    for fragment_data in STORY_BOARD:
        source_key = fragment_data["key"]
        source_fragment = fragments_map.get(source_key)

        if not source_fragment:
            print(f"  [Warning] Source fragment '{source_key}' not found for choices. Skipping.")
            continue

        for choice_data in fragment_data.get("choices", []):
            destination_key = choice_data["destination_key"]
            if destination_key not in fragments_map:
                print(f"  [Warning] Destination fragment '{destination_key}' not found. Skipping choice.")
                continue

            choice = NarrativeChoice(
                source_fragment_id=source_fragment.id,
                destination_fragment_key=destination_key,
                text=choice_data["text"]
            )
            session.add(choice)

    await session.commit()
    print("Narrative data populated successfully.")

async def main():
    # Initialize the database schema if it doesn't exist
    await init_db()
    
    # Get a session to interact with the database
    Session = await get_session()
    async with Session() as session:
        await populate_narrative_data(session)

if __name__ == "__main__":
    # This allows running the script directly to populate the database
    print("Running narrative population script...")
    asyncio.run(main())
