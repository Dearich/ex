import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.utils.callback_answer import CallbackAnswerMiddleware
from config import settings
from handlers import base, orders

async def main():
    # Настройка логирования
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    logger = logging.getLogger(__name__)

    # Инициализация бота и диспетчера
    bot = Bot(token=settings.BOT_TOKEN.get_secret_value())
    dp = Dispatcher(storage=MemoryStorage())

    # Регистрация обработчиков ошибок
    @dp.error()
    async def error_handler(event: types.ErrorEvent):
        logger.exception("Ошибка при обработке запроса:", exc_info=event.exception)
        try:
            # Пытаемся отправить сообщение об ошибке пользователю
            if event.update.callback_query:
                await event.update.callback_query.message.edit_text(
                    "Произошла ошибка. Пожалуйста, попробуйте еще раз.",
                    reply_markup=base.get_main_keyboard()
                )
            else:
                await event.update.message.answer(
                    "Произошла ошибка. Пожалуйста, попробуйте еще раз.",
                    reply_markup=base.get_main_keyboard()
                )
        except Exception as e:
            logger.error(f"Ошибка при отправке сообщения об ошибке: {e}")

    # Регистрация middleware
    dp.callback_query.middleware(CallbackAnswerMiddleware())

    # Регистрация роутеров
    dp.include_router(base.router)
    dp.include_router(orders.router)

    # Запуск бота
    try:
        logger.info("Бот запущен")
        await dp.start_polling(bot)
    finally:
        logger.info("Бот остановлен")
        await bot.session.close()

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.info("Бот остановлен") 