from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

# from ..services.narrative_service import NarrativeService
# from ..keyboards.narrative_kb import create_narrative_keyboard
# from ..utils.message_safety import safe_answer, safe_edit

router = Router(name="narrative_handler")

@router.message(F.text.lower() == "/historia")
async def start_story(message: Message, session: AsyncSession, state: FSMContext):
    """Starts or continues the narrative for the user."""
    # narrative_service = NarrativeService(session)
    # fragment = await narrative_service.get_user_current_fragment(message.from_user.id)
    # keyboard = create_narrative_keyboard(fragment)
    # await safe_answer(message, fragment.text, reply_markup=keyboard)
    await message.answer("Narrative module is under construction.")


@router.callback_query(F.data.startswith("narrative:decision:"))
async def handle_decision(callback: CallbackQuery, session: AsyncSession, state: FSMContext):
    """Handles a user's decision in the narrative."""
    decision_id = int(callback.data.split(":")[2])
    narrative_service = NarrativeService(session)
    new_fragment = await narrative_service.process_user_decision(callback.from_user.id, decision_id)
    
    if new_fragment:
        keyboard = create_narrative_keyboard(new_fragment)
        await safe_edit(callback.message, new_fragment.text, reply_markup=keyboard)
    else:
        # Handle cases where conditions are not met
        await callback.answer("You cannot make this choice right now.", show_alert=True)
