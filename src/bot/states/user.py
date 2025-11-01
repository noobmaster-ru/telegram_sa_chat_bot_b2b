from aiogram.fsm.state import StatesGroup, State

class UserState(StatesGroup):
    waiting_for_token = State()
    waiting_for_google_sheets_url = State()