# init_db.py
import asyncio
from database.models import Base
from database.session import engine
from core.logging import setup_logging, logger

async def init_models():
    setup_logging()
    logger.info("initializing_database_tables")
    
    try:
        async with engine.begin() as conn:
            # Удаляем старые таблицы (если они были) и создаем новые
            # ВНИМАНИЕ: Это удалит данные в PostgreSQL, если они там уже есть
            # await conn.run_sync(Base.metadata.drop_all) 
            await conn.run_sync(Base.metadata.create_all)
            
        logger.info("database_tables_created_successfully")
    except Exception as e:
        logger.error("database_initialization_failed", error=str(e))
    finally:
        await engine.dispose()

if __name__ == "__main__":
    asyncio.run(init_models())
