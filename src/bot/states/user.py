from aiogram.fsm.state import StatesGroup, State

class UserState(StatesGroup):
    token_handler = State()
    google_sheet_handler = State()
    
    service_account_handler = State()
    data_export_telegram = State()