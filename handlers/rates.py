from aiogram import types, Dispatcher
from aiogram.filters import Command
from services.exchange import ExchangeService
from keyboards.base import get_main_keyboard

async def show_rates(message: types.Message):
    """Показать текущие курсы валют"""
    exchange_service = ExchangeService()
    rates = await exchange_service.get_exchange_rates()
    
    text = "Текущие курсы валют к KZT:\n\n"
    text += f"🇷🇺 RUB: {rates['RUB']:.2f}\n"
    text += f"🇺🇸 USD: {rates['USD']:.2f}\n"
    text += f"🇪🇺 EUR: {rates['EUR']:.2f}"
    
    await message.answer(text, reply_markup=get_main_keyboard())

def register_rate_handlers(dp: Dispatcher):
    dp.message.register(show_rates, Command(commands=["rates"])) 