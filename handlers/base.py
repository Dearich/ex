from aiogram import types, Router, F
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from services.exchange import ExchangeService
from keyboards.base import get_main_keyboard

router = Router()

@router.message(CommandStart())
async def cmd_start(message: types.Message):
    """Обработчик команды /start"""
    await message.answer(
        f"👋 Привет, {message.from_user.first_name}!\n\n"
        "Я бот для обмена валют. Выберите действие:",
        reply_markup=get_main_keyboard()
    )

@router.message(Command("help"))
async def cmd_help(message: types.Message):
    """Обработчик команды /help"""
    help_text = (
        "🤖 Доступные команды:\n\n"
        "/start - Начать работу с ботом\n"
        "/help - Показать это сообщение\n\n"
        "Используйте кнопки меню для:\n"
        "💱 Просмотра курсов валют\n"
        "📝 Создания заявок на обмен\n"
        "📋 Управления своими заявками\n"
        "🔍 Поиска открытых заявок\n"
        "✅ Получения проверенного статуса"
    )
    await message.answer(help_text, reply_markup=get_main_keyboard())

@router.callback_query(F.data == "show_rates")
async def show_rates(callback: types.CallbackQuery):
    """Показ текущих курсов валют"""
    try:
        rates = await ExchangeService.get_exchange_rates()
        text = ExchangeService.format_rates_message(rates)
    except Exception as e:
        text = "❌ Сервис курсов валют временно недоступен.\nПожалуйста, попробуйте позже."
    
    await callback.message.edit_text(
        text,
        reply_markup=get_main_keyboard()
    )

@router.callback_query(F.data == "back_to_main")
async def back_to_main(callback: types.CallbackQuery, state: FSMContext):
    """Возврат в главное меню"""
    await state.clear()
    await callback.message.edit_text(
        "Выберите действие:",
        reply_markup=get_main_keyboard()
    )

@router.callback_query(F.data == "get_verified")
async def get_verified(callback: types.CallbackQuery):
    """Получение проверенного статуса"""
    admin_usernames = ["@admin1", "@admin2"]  # Замените на реальные юзернеймы админов
    
    text = (
        "ℹ️ Для получения проверенного статуса:\n\n"
        "1. Напишите любому из администраторов:\n"
        f"{', '.join(admin_usernames)}\n\n"
        "2. Администратор вышлет вам условия верификации\n"
        "3. После выполнения условий вы получите проверенный статус\n\n"
        "❗️ Проверенный статус повышает доверие к вашим заявкам"
    )
    
    await callback.message.edit_text(
        text,
        reply_markup=get_main_keyboard()
    ) 