from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from database.models import Trivia, TriviaQuestion, TriviaAttempt, TriviaUserAnswer
from datetime import datetime

class TriviaService:

    @staticmethod
    async def get_active_trivias(session: AsyncSession):
        result = await session.execute(select(Trivia).where(Trivia.is_active == True))
        return result.scalars().all()

    @staticmethod
    async def get_trivia_questions(session: AsyncSession, trivia_id: int):
        result = await session.execute(
            select(TriviaQuestion).where(TriviaQuestion.trivia_id == trivia_id).order_by(TriviaQuestion.order)
        )
        return result.scalars().all()

    @staticmethod
    async def create_attempt(session: AsyncSession, user_id: int, trivia_id: int):
        attempt = TriviaAttempt(user_id=user_id, trivia_id=trivia_id)
        session.add(attempt)
        await session.commit()
        await session.refresh(attempt)
        return attempt

    @staticmethod
    async def save_user_answer(session: AsyncSession, attempt_id: int, question_id: int, user_answer: str, is_correct: bool):
        user_answer_entry = TriviaUserAnswer(
            attempt_id=attempt_id, question_id=question_id, user_answer=user_answer, is_correct=is_correct
        )
        session.add(user_answer_entry)
        await session.commit()

    @staticmethod
    async def finalize_attempt(session: AsyncSession, attempt_id: int, total_correct: int):
        attempt = await session.get(TriviaAttempt, attempt_id)
        attempt.score = total_correct
        attempt.completed_at = datetime.utcnow()
        await session.commit()

    @staticmethod
    async def create_trivia(session: AsyncSession, data: dict):
        trivia = Trivia(title=data["title"], is_active=True)
        session.add(trivia)
        await session.flush()

        for q in data["questions"]:
            question = TriviaQuestion(
                question=q["text"], options=q["options"], correct_option=q["answer"],
                points=q["points"], exclusive_content=q["unlocks_content"], trivia_id=trivia.id
            )
            session.add(question)

        await session.commit()
