from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, FSInputFile
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession
from services.trivia_service import TriviaService
from keyboards.trivia_keyboards import trivia_selection_keyboard, trivia_question_keyboard
from services.trivia_states import TriviaStates
from utils.messages import TRIVIA_INTRO_MESSAGE, TRIVIA_COMPLETE_MESSAGE

router = Router()

@router.message(F.text == "Trivias")
async def show_trivia_menu(message: Message, session: AsyncSession):
    trivias = await TriviaService.get_active_trivias(session)
    await message.answer(TRIVIA_INTRO_MESSAGE, reply_markup=trivia_selection_keyboard(trivias))

@router.callback_query(F.data.startswith("start_trivia:"))
async def start_trivia(call: CallbackQuery, session: AsyncSession, state: FSMContext):
    trivia_id = int(call.data.split(":")[1])
    questions = await TriviaService.get_trivia_questions(session, trivia_id)
    attempt = await TriviaService.create_attempt(session, call.from_user.id, trivia_id)

    await state.update_data(
        questions=[q.id for q in questions],
        current=0,
        correct_answers=0,
        attempt_id=attempt.id,
        trivia_id=trivia_id
    )
    await call.answer()
    await send_next_question(call.message, questions, state)

async def send_next_question(message, questions, state):
    data = await state.get_data()
    current = data["current"]

    if current >= len(questions):
        await message.answer(TRIVIA_COMPLETE_MESSAGE.format(score=data["correct_answers"]))
        await state.clear()
        return

    question = questions[current]

    if question.media_type == "image":
        await message.answer_photo(FSInputFile(question.media_path), caption=question.question_text,
                                   reply_markup=trivia_question_keyboard(question.options))
    else:
        await message.answer(question.question_text,
                             reply_markup=trivia_question_keyboard(question.options))

    await state.set_state(TriviaStates.answering)

@router.callback_query(TriviaStates.answering, F.data.startswith("answer:"))
async def handle_answer(call: CallbackQuery, session: AsyncSession, state: FSMContext):
    user_answer = call.data.split(":")[1]
    data = await state.get_data()
    current = data["current"]
    questions_ids = data["questions"]
    question_id = questions_ids[current]
    question = await session.get(TriviaQuestion, question_id)

    is_correct = user_answer == question.correct_answer
    if is_correct:
        data["correct_answers"] += 1

    await TriviaService.save_user_answer(session, data["attempt_id"], question_id, user_answer, is_correct)
    data["current"] += 1
    await state.update_data(data)

    questions = await TriviaService.get_trivia_questions(session, data["trivia_id"])
    await send_next_question(call.message, questions, state)
    await call.answer()
