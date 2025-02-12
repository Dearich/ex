from typing import Dict, List, Tuple
import aiohttp
from datetime import datetime, timedelta
import logging

class ExchangeService:
    _rates_cache: Dict[str, float] = {}
    _last_update: datetime = datetime.min
    _cache_duration = timedelta(minutes=5)

    @classmethod
    async def get_exchange_rates(cls) -> Dict[str, Tuple[str, float]]:
        """Получение актуальных курсов валют с флагами стран"""
        if (datetime.now() - cls._last_update) < cls._cache_duration and cls._rates_cache:
            return cls._rates_cache

        try:
            async with aiohttp.ClientSession() as session:
                url = "https://api.exchangerate-api.com/v4/latest/USD"
                async with session.get(url) as response:
                    if response.status != 200:
                        raise Exception(f"API вернул статус {response.status}")
                    
                    data = await response.json()
                    rates = data['rates']
                    
                    # Рассчитываем кросс-курсы
                    cls._rates_cache = {
                        'RUB_KZT': ('🇷🇺 RUB → 🇰🇿 KZT', rates['KZT'] / rates['RUB']),
                        'USD_RUB': ('🇺🇸 USD → 🇷🇺 RUB', rates['RUB']),
                        'EUR_RUB': ('🇪🇺 EUR → 🇷🇺 RUB', rates['RUB'] / rates['EUR']),
                        'USD_KZT': ('🇺🇸 USD → 🇰🇿 KZT', rates['KZT']),
                        'EUR_KZT': ('🇪🇺 EUR → 🇰🇿 KZT', rates['KZT'] / rates['EUR'])
                    }
                    cls._last_update = datetime.now()
                    return cls._rates_cache
        except Exception as e:
            logging.error(f"Ошибка при получении курсов валют: {e}")
            raise Exception("Сервис курсов валют временно недоступен")

    @staticmethod
    def format_rates_message(rates: Dict[str, Tuple[str, float]]) -> str:
        """Форматирование сообщения с курсами валют"""
        text = "💱 Текущие курсы валют:\n" \
               "(по данным exchangerate-api.com)\n\n"
        
        # Определяем порядок отображения курсов
        order = ['RUB_KZT', 'USD_RUB', 'EUR_RUB', 'USD_KZT', 'EUR_KZT']
        for key in order:
            name, rate = rates[key]
            text += f"{name}: {rate:.2f}\n"
        
        text += "\n⚠️ Курсы обновляются каждые 5 минут"
        return text

    @staticmethod
    def get_available_currencies() -> List[Tuple[str, str]]:
        return [
            ('KZT', '🇰🇿 Тенге'),
            ('RUB', '🇷🇺 Рубль'),
            ('USD', '🇺🇸 Доллар'),
            ('EUR', '🇪🇺 Евро')
        ]

    @staticmethod
    def get_payment_methods() -> List[str]:
        return [
            'Kaspi Bank 🟡',
            'Halyk Bank 💛',
            'Jusan Bank 🔵',
            'QIWI 🥝',
            'Сбербанк 💚',
            'Тинькофф 💎'
        ]

    @staticmethod
    def get_execution_times() -> List[Tuple[timedelta, str]]:
        return [
            (timedelta(minutes=30), '30 минут'),
            (timedelta(hours=1), '1 час'),
            (timedelta(hours=2), '2 часа'),
            (timedelta(hours=4), '4 часа'),
            (timedelta(hours=24), '24 часа')
        ] 