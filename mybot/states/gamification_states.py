from aiogram.fsm.state import StatesGroup, State

class LorePieceAdminStates(StatesGroup):
    creating_code_name = State()
    creating_title = State()
    creating_description = State()
    creating_category = State()
    confirming_main_story = State()
    choosing_content_type = State()
    entering_text_content = State()
    uploading_file_content = State()

    # States for editing an existing lore piece
    editing_title = State()
    editing_description = State()
    editing_category = State()
    editing_is_main_story = State()
    editing_content_type = State()
    editing_text_content = State()
    editing_file_content = State()
