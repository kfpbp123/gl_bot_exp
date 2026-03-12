# bot/middlewares/db.py
from typing import Any, Awaitable, Callable, Dict
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject
from sqlalchemy.ext.asyncio import async_sessionmaker
from database.repositories import UserRepository, PostRepository

class DbSessionMiddleware(BaseMiddleware):
    def __init__(self, session_pool: async_sessionmaker):
        super().__init__()
        self.session_pool = session_pool

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        async with self.session_pool() as session:
            # Инъекция репозиториев в хэндлер
            data["user_repo"] = UserRepository(session)
            data["post_repo"] = PostRepository(session)
            data["db_session"] = session
            
            return await handler(event, data)
