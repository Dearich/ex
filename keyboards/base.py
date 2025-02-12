from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from services.exchange import ExchangeService
from services.orders import OrderService
from models.order import OrderStatus

def get_main_keyboard() -> InlineKeyboardMarkup:
    """Главная клавиатура бота"""
    kb = InlineKeyboardBuilder()
    kb.button(text="💱 Курсы валют", callback_data="show_rates")
    kb.button(text="📝 Создать заявку", callback_data="create_order")
    kb.button(text="📋 Мои заявки", callback_data="my_orders")
    kb.button(text="🔍 Открытые заявки", callback_data="available_orders")
    kb.button(text="✅ Получить проверенный статус", callback_data="get_verified")
    kb.adjust(1)  # Кнопки в один столбец
    return kb.as_markup()

def get_currency_keyboard(for_select: bool = False) -> InlineKeyboardMarkup:
    """Клавиатура выбора валюты"""
    kb = InlineKeyboardBuilder()
    
    currencies = ExchangeService.get_available_currencies()
    for code, name in currencies:
        kb.button(
            text=name,
            callback_data=f"select_currency_{code}" if for_select else f"filter_currency_{code}"
        )
    
    kb.button(text="↩️ Назад", callback_data="back_to_main")
    kb.adjust(2, 2, 1)  # 2 кнопки в ряд, последняя отдельно
    return kb.as_markup()

def get_payment_methods_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура выбора способа оплаты"""
    kb = InlineKeyboardBuilder()
    
    for method in ExchangeService.get_payment_methods():
        kb.button(text=method, callback_data=f"payment_{method}")
    
    kb.button(text="↩️ Назад", callback_data="back_to_main")
    kb.adjust(2, 2, 2, 1)  # По 2 кнопки в ряд
    return kb.as_markup()

def get_execution_time_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура выбора времени исполнения"""
    kb = InlineKeyboardBuilder()
    
    for time, text in ExchangeService.get_execution_times():
        kb.button(text=text, callback_data=f"time_{time.total_seconds()}")
    
    kb.button(text="↩️ Назад", callback_data="back_to_main")
    kb.adjust(2, 2, 1)
    return kb.as_markup()

def get_order_actions_keyboard(order_id: int, is_creator: bool, user_id: int = None) -> InlineKeyboardMarkup:
    """Клавиатура действий с заявкой"""
    kb = InlineKeyboardBuilder()
    order = OrderService.get_order(order_id)
    
    if order.status == OrderStatus.ACTIVE:
        if is_creator:
            kb.button(text="❌ Отменить заявку", callback_data=f"cancel_{order_id}")
        else:
            kb.button(text="📝 Взять в работу", callback_data=f"take_{order_id}")
    
    elif order.status == OrderStatus.IN_PROGRESS:
        if is_creator:
            kb.button(text="✅ Подтвердить выполнение", callback_data=f"complete_{order_id}")
            kb.button(text="❌ Отменить заявку", callback_data=f"cancel_{order_id}")
        elif user_id and order.executor_id == user_id:
            kb.button(text="✅ Отметить как выполненную", callback_data=f"mark_done_{order_id}")
    
    # Для завершенных и отмененных заявок кнопки действий не показываем
    
    kb.button(text="↩️ К списку заявок", callback_data="back_to_orders")
    kb.adjust(1)
    return kb.as_markup() 