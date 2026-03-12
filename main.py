# main.py
import asyncio
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.redis import RedisStorage, Redis
from core.config import settings
from core.logging import setup_logging, logger
from bot.middlewares.db import DbSessionMiddleware
from database.session import async_session
from bot.handlers import common, posts

async def main():
    # 1. Настройка логирования
    setup_logging()
    
    # 2. Инициализация Redis (используется для FSM)
    # redis://localhost:6379/0
    redis = Redis.from_url(str(settings.REDIS_URL))
    storage = RedisStorage(redis)

    # 3. Настройка бота и диспетчера
    bot = Bot(token=settings.BOT_TOKEN.get_secret_value())
    dp = Dispatcher(storage=storage)

    # 4. Регистрация мидлварей (авто-БД)
    dp.update.middleware(DbSessionMiddleware(async_session))

    # 5. Регистрация хэндлеров
    dp.include_router(common.router)
    dp.include_router(posts.router)

    # 6. Запуск бота
    me = await bot.get_me()
    logger.info("bot_started", username=me.username)
    
    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("bot_stopped")
