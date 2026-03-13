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
    
    # 2. Инициализация БД (автоматическое создание таблиц)
    from database.models import Base
    from database.session import engine
    logger.info("initializing_database")
    try:
        async with engine.begin() as conn:
            # Создаем таблицы, если их нет
            await conn.run_sync(Base.metadata.create_all)
        logger.info("database_initialized_successfully")
    except Exception as e:
        logger.error("database_initialization_failed", error=str(e))
        # Не останавливаем бота, но логируем критическую ошибку
    
    # 3. Инициализация Redis (используется для FSM)
    try:
        redis = Redis.from_url(str(settings.REDIS_URL))
        # Проверяем соединение
        await redis.ping()
        storage = RedisStorage(redis)
        logger.info("redis_connected_successfully")
    except Exception as e:
        logger.error("redis_connection_failed", error=str(e))
        # Если Redis недоступен, можно откатиться на MemoryStorage (опционально)
        from aiogram.fsm.storage.memory import MemoryStorage
        storage = MemoryStorage()
        logger.warning("using_memory_storage_as_fallback")

    # 4. Настройка бота и диспетчера
    bot = Bot(token=settings.BOT_TOKEN.get_secret_value())
    dp = Dispatcher(storage=storage)

    # 4. Регистрация мидлварей (авто-БД)
    dp.update.middleware(DbSessionMiddleware(async_session))

    # 5. Регистрация хэндлеров
    dp.include_router(common.router)
    dp.include_router(posts.router)

    # 6. Запуск шедулера (в фоне)
    from bot.scheduler import scheduler_loop
    asyncio.create_task(scheduler_loop(bot))

    # 7. Запуск бота
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
