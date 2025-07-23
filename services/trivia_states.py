from aiogram.fsm.state import StatesGroup, State

class TriviaStates(StatesGroup):
    answering = State()
