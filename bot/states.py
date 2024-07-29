from aiogram.fsm.state import State, StatesGroup

class UserStates(StatesGroup):
    get_excel = State()
    get_theme = State()