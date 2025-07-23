from aiogram.fsm.state import StatesGroup, State

class CreateTrivia(StatesGroup):
    waiting_for_title = State()
    waiting_for_total_questions = State()
    waiting_for_question_text = State()
    waiting_for_question_type = State()
    waiting_for_question_options = State()
    waiting_for_correct_answer = State()
    waiting_for_points = State()
    waiting_for_unlock_content = State()
    confirm_trivia = State()
