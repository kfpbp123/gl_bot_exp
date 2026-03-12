# database/session.py
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from core.config import settings

# Создаем асинхронный движок
engine = create_async_engine(
    str(settings.DATABASE_URL),
    echo=False,
    future=True,
)

# Фабрика асинхронных сессий
async_session = async_sessionmaker(
    engine, 
    class_=AsyncSession, 
    expire_on_commit=False
)

async def get_session() -> AsyncSession:
    async with async_session() as session:
        yield session
