from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession
from services.trivia_service import TriviaService
from keyboards.admin_trivia_kb import (
    trivia_admin_main_kb,
    question_type_kb,
    yes_no_kb,
    confirm_trivia_kb,
)
from states.trivia_states import CreateTrivia
from utils.menu_utils import update_menu
from keyboards.common import get_back_kb
import logging

logger = logging.getLogger(__name__)
router = Router()


@router.message(F.text == "🛠️ Administrar Trivias")
async def admin_trivia_menu(message: Message):
    await message.answer("📚 Menú de administración de Trivias:", reply_markup=trivia_admin_main_kb())


@router.callback_query(F.data == "list_trivias")
async def list_trivias(call: CallbackQuery, session: AsyncSession):
    trivias = await TriviaService.get_active_trivias(session)
    text = "\n".join(f"{t.id}. {t.title}" for t in trivias) or "Sin trivias activas."
    await call.message.edit_text(
        f"📚 *Trivias activas:*\n{text}", parse_mode="Markdown", reply_markup=trivia_admin_main_kb()
    )


@router.callback_query(F.data == "create_trivia")
async def create_trivia(call: CallbackQuery, state: FSMContext):
    await state.set_state(CreateTrivia.waiting_for_title)
    await call.message.edit_text("✏️ Envía el título para la nueva trivia:")


@router.message(CreateTrivia.waiting_for_title)
async def trivia_title_received(message: Message, state: FSMContext):
    await state.update_data(title=message.text, questions=[])
    await state.set_state(CreateTrivia.waiting_for_total_questions)
    await message.answer("🔢 ¿Cuántas preguntas tendrá esta trivia? (ej: 5)")


@router.message(CreateTrivia.waiting_for_total_questions)
async def total_questions_received(message: Message, state: FSMContext):
    if not message.text.isdigit():
        return await message.answer("⚠️ Ingresa solo números.")
    await state.update_data(total_questions=int(message.text), current_question=1)
    await state.set_state(CreateTrivia.waiting_for_question_text)
    await message.answer("📝 Escribe la primera pregunta:")


@router.message(CreateTrivia.waiting_for_question_text)
async def question_text_received(message: Message, state: FSMContext):
    await state.update_data(question_text=message.text)
    await state.set_state(CreateTrivia.waiting_for_question_type)
    await message.answer("🧐 ¿Qué tipo de pregunta es?", reply_markup=question_type_kb())


@router.callback_query(CreateTrivia.waiting_for_question_type)
async def question_type_received(call: CallbackQuery, state: FSMContext):
    qtype = call.data
    await state.update_data(question_type=qtype)
    if qtype == "open":
        await state.set_state(CreateTrivia.waiting_for_correct_answer)
        await call.message.edit_text("✔️ Escribe la respuesta correcta:")
    else:
        await state.set_state(CreateTrivia.waiting_for_question_options)
        await call.message.edit_text("🔠 Envía las opciones separadas por comas (ej: Rojo,Azul,Verde):")


@router.message(CreateTrivia.waiting_for_question_options)
async def options_received(message: Message, state: FSMContext):
    options = [opt.strip() for opt in message.text.split(",")]
    await state.update_data(options=options)
    await state.set_state(CreateTrivia.waiting_for_correct_answer)
    await message.answer(
        "✅ Indica cuál es la respuesta correcta exactamente como la escribiste en las opciones:"
    )


@router.message(CreateTrivia.waiting_for_correct_answer)
async def correct_answer_received(message: Message, state: FSMContext):
    await state.update_data(correct_answer=message.text)
    await state.set_state(CreateTrivia.waiting_for_points)
    await message.answer("💎 ¿Cuántos puntos vale esta pregunta?")


@router.message(CreateTrivia.waiting_for_points)
async def points_received(message: Message, state: FSMContext):
    if not message.text.isdigit():
        return await message.answer("⚠️ Ingresa solo números.")
    await state.update_data(points=int(message.text))
    await state.set_state(CreateTrivia.waiting_for_unlock_content)
    await message.answer("🔓 ¿Esta pregunta desbloquea contenido?", reply_markup=yes_no_kb())


@router.callback_query(CreateTrivia.waiting_for_unlock_content)
async def unlock_content_received(call: CallbackQuery, state: FSMContext):
    unlocks = call.data == "yes"
    data = await state.get_data()
    data["questions"].append(
        {
            "text": data["question_text"],
            "type": data["question_type"],
            "options": data.get("options", []),
            "answer": data["correct_answer"],
            "points": data["points"],
            "unlocks_content": unlocks,
        }
    )
    if data["current_question"] >= data["total_questions"]:
        await state.update_data(data)
        await state.set_state(CreateTrivia.confirm_trivia)
        await call.message.edit_text(
            "🎯 Trivia lista para guardar. ¿Confirmar creación?", reply_markup=confirm_trivia_kb()
        )
    else:
        data["current_question"] += 1
        await state.update_data(data, question_text=None, question_type=None, options=None)
        await state.set_state(CreateTrivia.waiting_for_question_text)
        await call.message.edit_text(f"📝 Escribe la pregunta #{data['current_question']}:")


@router.callback_query(CreateTrivia.confirm_trivia)
async def confirm_creation(call: CallbackQuery, state: FSMContext, session: AsyncSession):
    if call.data == "confirm":
        data = await state.get_data()
        await TriviaService.create_trivia(session, data)
        await call.message.edit_text("✅ Trivia creada exitosamente.")
    else:
        await call.message.edit_text("❌ Creación cancelada.")
    await state.clear()
