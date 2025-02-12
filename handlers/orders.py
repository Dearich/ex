from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from services.orders import OrderService
from services.exchange import ExchangeService
from keyboards.base import (
    get_main_keyboard, get_currency_keyboard,
    get_payment_methods_keyboard, get_execution_time_keyboard,
    get_order_actions_keyboard
)
from typing import List
from models.order import Order, OrderStatus
from datetime import timedelta
import logging

router = Router()

class OrderStates(StatesGroup):
    select_currency_from = State()
    select_currency_to = State()
    enter_amount = State()
    enter_rate = State()
    select_payment_method = State()
    select_execution_time = State()
    confirm_order = State()

@router.callback_query(F.data == "create_order")
async def start_order_creation(callback: types.CallbackQuery, state: FSMContext):
    """Начало создания заявки"""
    await state.set_state(OrderStates.select_currency_from)
    await callback.message.edit_text(
        "Выберите валюту, которую хотите обменять:",
        reply_markup=get_currency_keyboard(for_select=True)
    )

@router.callback_query(F.data.startswith("select_currency_"))
async def process_currency_selection(callback: types.CallbackQuery, state: FSMContext):
    """Обработка выбора валюты"""
    current_state = await state.get_state()
    currency = callback.data.split('_')[-1]
    
    if current_state == OrderStates.select_currency_from:
        await state.update_data(currency_from=currency)
        await state.set_state(OrderStates.select_currency_to)
        await callback.message.edit_text(
            "Выберите валюту, которую хотите получить:",
            reply_markup=get_currency_keyboard(for_select=True)
        )
    elif current_state == OrderStates.select_currency_to:
        await state.update_data(currency_to=currency)
        await state.set_state(OrderStates.enter_amount)
        await callback.message.edit_text(
            "Введите сумму для обмена:",
            reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[
                [types.InlineKeyboardButton(text="↩️ Назад", callback_data="back_to_main")]
            ])
        )

@router.message(OrderStates.enter_amount)
async def process_amount(message: types.Message, state: FSMContext):
    """Обработка ввода суммы"""
    try:
        amount = float(message.text)
        if amount <= 0:
            raise ValueError
        
        await state.update_data(amount=amount)
        await state.set_state(OrderStates.enter_rate)
        
        # Получаем текущий курс для подсказки
        data = await state.get_data()
        rates = await ExchangeService.get_exchange_rates()
        
        # Определяем ключ для поиска курса
        from_currency = data['currency_from']
        to_currency = data['currency_to']
        rate_key = f"{from_currency}_{to_currency}"
        reverse_key = f"{to_currency}_{from_currency}"
        
        # Получаем и форматируем курс
        if rate_key in rates:
            _, current_rate = rates[rate_key]
            rate_text = f"{current_rate:.2f}"
        elif reverse_key in rates:
            _, reverse_rate = rates[reverse_key]
            current_rate = 1 / reverse_rate
            rate_text = f"{current_rate:.2f}"
        else:
            rate_text = "не найден"
        
        # Удаляем предыдущее сообщение
        await message.delete()
        
        # Обновляем сообщение с меню
        await message.answer(
            f"Введите желаемый курс обмена:\n"
            f"Текущий рыночный курс {from_currency} → {to_currency}: {rate_text}",
            reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[
                [types.InlineKeyboardButton(text="↩️ Назад", callback_data="back_to_main")]
            ])
        )
    except ValueError:
        await message.answer("Пожалуйста, введите корректное число.")

@router.message(OrderStates.enter_rate)
async def process_rate(message: types.Message, state: FSMContext):
    """Обработка ввода курса"""
    try:
        rate = float(message.text)
        if rate <= 0:
            raise ValueError
        
        await state.update_data(rate=rate)
        await state.set_state(OrderStates.select_payment_method)
        await message.answer(
            "Выберите способ оплаты:",
            reply_markup=get_payment_methods_keyboard()
        )
    except ValueError:
        await message.answer("Пожалуйста, введите корректное число.")

@router.callback_query(F.data.startswith("payment_"))
async def process_payment_method(callback: types.CallbackQuery, state: FSMContext):
    """Обработка выбора способа оплаты"""
    payment_method = callback.data.replace("payment_", "")
    await state.update_data(payment_method=payment_method)
    await state.set_state(OrderStates.select_execution_time)
    await callback.message.edit_text(
        "Выберите срок исполнения заявки:",
        reply_markup=get_execution_time_keyboard()
    )

@router.callback_query(F.data.startswith("time_"))
async def process_execution_time(callback: types.CallbackQuery, state: FSMContext):
    """Обработка выбора времени исполнения"""
    seconds = float(callback.data.replace("time_", ""))
    await state.update_data(execution_time=seconds)
    
    # Показываем подтверждение создания заявки
    data = await state.get_data()
    confirmation_text = (
        "📝 Подтвердите создание заявки:\n\n"
        f"Обмен: {data['currency_from']} → {data['currency_to']}\n"
        f"Сумма: {data['amount']:.2f} {data['currency_from']}\n"
        f"Курс: {data['rate']:.2f}\n"
        f"Способ оплаты: {data['payment_method']}\n"
        f"Срок исполнения: {data['execution_time']/3600:.1f} ч"
    )
    
    await state.set_state(OrderStates.confirm_order)
    await callback.message.edit_text(
        confirmation_text,
        reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[
            [types.InlineKeyboardButton(text="✅ Подтвердить", callback_data="confirm_order")],
            [types.InlineKeyboardButton(text="❌ Отменить", callback_data="back_to_main")]
        ])
    )

@router.callback_query(F.data == "confirm_order", OrderStates.confirm_order)
async def confirm_order(callback: types.CallbackQuery, state: FSMContext):
    """Подтверждение создания заявки"""
    data = await state.get_data()
    
    # Создаем заявку
    order = OrderService.create_order(
        creator_id=callback.from_user.id,
        creator_username=callback.from_user.username or "Неизвестный",
        **data
    )
    
    await state.clear()
    await callback.message.edit_text(
        "✅ Заявка успешно создана!",
        reply_markup=get_main_keyboard()
    )

@router.callback_query(F.data == "my_orders")
async def show_my_orders_menu(callback: types.CallbackQuery):
    """Показать меню выбора типа заявок"""
    kb = InlineKeyboardBuilder()
    
    kb.button(text="📝 Созданные мной", callback_data="created_orders")
    kb.button(text="🔨 На исполнении", callback_data="executing_orders")
    kb.button(text="↩️ Назад", callback_data="back_to_main")
    kb.adjust(1)
    
    await callback.message.edit_text(
        "Выберите тип заявок для просмотра:",
        reply_markup=kb.as_markup()
    )

@router.callback_query(F.data == "created_orders")
async def show_created_orders(callback: types.CallbackQuery):
    """Показать созданные пользователем заявки"""
    orders = [order for order in OrderService.get_user_orders(callback.from_user.id)
             if order.creator_id == callback.from_user.id]
    
    if not orders:
        await callback.message.edit_text(
            "У вас пока нет созданных заявок.",
            reply_markup=get_orders_menu_keyboard()
        )
        return
    
    text = "📝 Ваши созданные заявки:\n\n"
    kb = InlineKeyboardBuilder()
    
    for order in orders:
        status_emoji = {
            OrderStatus.ACTIVE: "🟢",
            OrderStatus.IN_PROGRESS: "🟡",
            OrderStatus.COMPLETED: "✅",
            OrderStatus.CANCELLED: "❌"
        }.get(order.status, "⚪️")
        
        kb.button(
            text=f"{status_emoji} {order.currency_from} → {order.currency_to} ({order.amount:.2f})",
            callback_data=f"view_order_{order.id}"
        )
    
    kb.button(text="↩️ К выбору", callback_data="my_orders")
    kb.adjust(1)
    
    await callback.message.edit_text(text, reply_markup=kb.as_markup())

@router.callback_query(F.data == "executing_orders")
async def show_executing_orders(callback: types.CallbackQuery):
    """Показать заявки на исполнении"""
    orders = [order for order in OrderService.get_user_orders(callback.from_user.id)
             if order.executor_id == callback.from_user.id]
    
    if not orders:
        await callback.message.edit_text(
            "У вас пока нет заявок на исполнении.",
            reply_markup=get_orders_menu_keyboard()
        )
        return
    
    text = "🔨 Заявки на вашем исполнении:\n\n"
    kb = InlineKeyboardBuilder()
    
    for order in orders:
        status_emoji = {
            OrderStatus.ACTIVE: "🟢",
            OrderStatus.IN_PROGRESS: "🟡",
            OrderStatus.COMPLETED: "✅",
            OrderStatus.CANCELLED: "❌"
        }.get(order.status, "⚪️")
        
        kb.button(
            text=f"{status_emoji} {order.currency_from} → {order.currency_to} ({order.amount:.2f})",
            callback_data=f"view_order_{order.id}"
        )
    
    kb.button(text="↩️ К выбору", callback_data="my_orders")
    kb.adjust(1)
    
    await callback.message.edit_text(text, reply_markup=kb.as_markup())

def get_orders_menu_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура для меню заявок"""
    kb = InlineKeyboardBuilder()
    kb.button(text="↩️ К выбору", callback_data="my_orders")
    kb.button(text="🏠 В главное меню", callback_data="back_to_main")
    kb.adjust(1)
    return kb.as_markup()

@router.callback_query(F.data == "available_orders")
async def show_available_orders_menu(callback: types.CallbackQuery):
    """Показать меню выбора фильтров для доступных заявок"""
    kb = InlineKeyboardBuilder()
    
    kb.button(text="🔄 Показать все", callback_data="show_all_orders")
    kb.button(text="💱 Фильтр по валюте", callback_data="filter_by_currency")
    kb.button(text="↩️ Назад", callback_data="back_to_main")
    kb.adjust(1)
    
    await callback.message.edit_text(
        "Выберите способ отображения заявок:",
        reply_markup=kb.as_markup()
    )

@router.callback_query(F.data == "show_all_orders")
async def show_all_orders(callback: types.CallbackQuery):
    """Показать все доступные заявки"""
    orders = OrderService.get_available_orders()
    await show_orders_list(callback, orders, "📋 Доступные заявки:\n\n")

@router.callback_query(F.data == "filter_by_currency")
async def show_currency_filter(callback: types.CallbackQuery):
    """Показать фильтр по валютам"""
    await callback.message.edit_text(
        "Выберите валюту для фильтрации:",
        reply_markup=get_currency_keyboard(for_select=False)
    )

@router.callback_query(F.data.startswith("filter_currency_"))
async def apply_currency_filter(callback: types.CallbackQuery):
    """Применить фильтр по валюте"""
    currency = callback.data.split('_')[-1]
    orders = OrderService.get_available_orders(currency_from=currency)
    await show_orders_list(
        callback, 
        orders, 
        f"📋 Заявки на обмен {currency}:\n\n"
    )

@router.callback_query(F.data.startswith("view_order_"))
async def view_order(callback: types.CallbackQuery):
    """Просмотр детальной информации о заявке"""
    order_id = int(callback.data.split('_')[-1])
    order = OrderService.get_order(order_id)
    
    if not order:
        await callback.message.edit_text(
            "❌ Заявка не найдена",
            reply_markup=get_main_keyboard()
        )
        return
    
    is_creator = order.creator_id == callback.from_user.id
    
    # Добавляем эмодзи статуса
    status_emoji = {
        OrderStatus.ACTIVE: "🟢",
        OrderStatus.IN_PROGRESS: "🟡",
        OrderStatus.COMPLETED: "✅",
        OrderStatus.CANCELLED: "❌"
    }.get(order.status, "⚪️")
    
    text = (
        f"📝 Заявка №{order.id}\n\n"
        f"Статус: {status_emoji} {order.status.value}\n"
        f"Создатель: @{order.creator_username}\n"
        f"Обмен: {order.currency_from} → {order.currency_to}\n"
        f"Сумма: {order.amount:.2f} {order.currency_from}\n"
        f"Курс: {order.rate:.2f}\n"
        f"Способ оплаты: {order.payment_method}\n"
        f"Срок исполнения: {order.execution_time/3600:.1f} ч\n"
    )
    
    if order.executor_username:
        text += f"Исполнитель: @{order.executor_username}\n"
    
    await callback.message.edit_text(
        text,
        reply_markup=get_order_actions_keyboard(order.id, is_creator, callback.from_user.id)
    )

@router.callback_query(F.data.startswith("take_"))
async def take_order(callback: types.CallbackQuery):
    """Взять заявку в работу"""
    order_id = int(callback.data.split('_')[-1])
    order = OrderService.get_order(order_id)
    
    if not order or order.status != OrderStatus.ACTIVE:
        await callback.answer("❌ Заявка недоступна")
        return
    
    OrderService.update_order(
        order_id,
        status=OrderStatus.IN_PROGRESS,
        executor_id=callback.from_user.id,
        executor_username=callback.from_user.username
    )
    
    # Отправляем уведомление исполнителю
    await callback.message.edit_text(
        "✅ Вы взяли заявку в работу!\n"
        f"Свяжитесь с создателем заявки: @{order.creator_username}",
        reply_markup=get_main_keyboard()
    )
    
    # Отправляем уведомление создателю заявки с кнопками действий
    try:
        kb = InlineKeyboardBuilder()
        kb.button(text="✅ Подтвердить выполнение", callback_data=f"complete_{order_id}")
        kb.button(text="❌ Отменить заявку", callback_data=f"cancel_{order_id}")
        kb.button(text="👁️ Просмотреть заявку", callback_data=f"view_order_{order_id}")
        kb.adjust(1)
        
        await callback.bot.send_message(
            order.creator_id,
            f"📋 Ваша заявка №{order.id} взята в работу!\n\n"
            f"Детали заявки:\n"
            f"Обмен: {order.currency_from} → {order.currency_to}\n"
            f"Сумма: {order.amount:.2f} {order.currency_from}\n"
            f"Курс: {order.rate:.2f}\n\n"
            f"Исполнитель: @{callback.from_user.username}\n"
            "Ожидайте, исполнитель свяжется с вами!",
            reply_markup=kb.as_markup()
        )
    except Exception as e:
        logging.error(f"Ошибка при отправке уведомления создателю заявки: {e}")
        await callback.answer(
            "⚠️ Не удалось отправить уведомление создателю заявки",
            show_alert=True
        )

@router.callback_query(F.data.startswith("complete_"))
async def complete_order(callback: types.CallbackQuery):
    """Подтверждение выполнения заявки"""
    order_id = int(callback.data.split('_')[-1])
    order = OrderService.get_order(order_id)
    
    if not order or order.creator_id != callback.from_user.id:
        await callback.answer("❌ У вас нет прав на это действие")
        return
    
    OrderService.update_order(
        order_id,
        status=OrderStatus.COMPLETED
    )
    
    await callback.message.edit_text(
        "✅ Заявка помечена как выполненная!",
        reply_markup=get_main_keyboard()
    )

@router.callback_query(F.data.startswith("cancel_"))
async def cancel_order(callback: types.CallbackQuery):
    """Отмена заявки"""
    order_id = int(callback.data.split('_')[-1])
    order = OrderService.get_order(order_id)
    
    if not order or order.creator_id != callback.from_user.id:
        await callback.answer("❌ У вас нет прав на это действие")
        return
    
    OrderService.update_order(
        order_id,
        status=OrderStatus.CANCELLED
    )
    
    await callback.message.edit_text(
        "❌ Заявка отменена",
        reply_markup=get_main_keyboard()
    )

@router.callback_query(F.data == "back_to_orders")
async def back_to_orders(callback: types.CallbackQuery):
    """Возврат к списку заявок"""
    await show_my_orders_menu(callback)

async def show_orders_list(callback: types.CallbackQuery, orders: List[Order], header_text: str):
    """Вспомогательная функция для отображения списка заявок"""
    if not orders:
        await callback.message.edit_text(
            "Нет доступных заявок.",
            reply_markup=get_main_keyboard()
        )
        return
    
    kb = InlineKeyboardBuilder()
    for order in orders:
        kb.button(
            text=(f"{order.currency_from} → {order.currency_to} "
                  f"({order.amount:.2f} @ {order.rate:.2f})"),
            callback_data=f"view_order_{order.id}"
        )
    
    kb.button(text="↩️ Назад", callback_data="back_to_main")
    kb.adjust(1)
    
    await callback.message.edit_text(
        header_text,
        reply_markup=kb.as_markup()
    )

@router.callback_query(F.data.startswith("mark_done_"))
async def mark_done(callback: types.CallbackQuery):
    """Отметка о выполнении от исполнителя"""
    order_id = int(callback.data.split('_')[-1])
    order = OrderService.get_order(order_id)
    
    if not order or order.executor_id != callback.from_user.id:
        await callback.answer("❌ У вас нет прав на это действие")
        return
    
    # Отправляем уведомление создателю
    try:
        await callback.bot.send_message(
            order.creator_id,
            f"📋 Исполнитель отметил заявку №{order.id} как выполненную!\n\n"
            f"Детали заявки:\n"
            f"Обмен: {order.currency_from} → {order.currency_to}\n"
            f"Сумма: {order.amount:.2f} {order.currency_from}\n"
            f"Курс: {order.rate:.2f}\n\n"
            "Пожалуйста, подтвердите выполнение заявки в разделе 'Мои заявки'"
        )
    except Exception as e:
        logging.error(f"Ошибка при отправке уведомления создателю заявки: {e}")
    
    await callback.message.edit_text(
        "✅ Вы отметили заявку как выполненную!\n"
        "Ожидайте подтверждения от создателя заявки.",
        reply_markup=get_main_keyboard()
    ) 