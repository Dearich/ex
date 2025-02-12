from aiogram.fsm.state import State, StatesGroup

class OrderStates(StatesGroup):
    select_currency_from = State()
    select_currency_to = State()
    enter_amount = State()
    enter_rate = State()
    select_payment_method = State()
    confirm_order = State() 