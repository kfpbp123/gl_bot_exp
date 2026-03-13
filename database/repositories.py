# database/repositories.py
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.postgresql import insert
from database.models import User, Channel, Post
from core.logging import logger
from datetime import datetime

class BaseRepository:
    def __init__(self, session: AsyncSession):
        self.session = session
        self._logger = logger.bind(repository=self.__class__.__name__)

class UserRepository(BaseRepository):
    async def get_user(self, user_id: int) -> User | None:
        result = await self.session.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    async def upsert_user(self, user_id: int, username: str | None, language: str = "ru"):
        """Создает или обновляет пользователя"""
        stmt = insert(User).values(
            id=user_id, 
            username=username, 
            language=language
        ).on_conflict_do_update(
            index_elements=[User.id],
            set_={
                "username": username,
                "language": language
            }
        )
        await self.session.execute(stmt)
        await self.session.commit()

class PostRepository(BaseRepository):
    async def create_post(self, user_id: int, text: str, media_url: str | None = None) -> Post:
        post = Post(user_id=user_id, text=text, media_url=media_url, status="draft")
        self.session.add(post)
        await self.session.commit()
        await self.session.refresh(post)
        return post

    async def get_scheduled_posts(self) -> list[Post]:
        """Возвращает посты, время публикации которых пришло"""
        result = await self.session.execute(
            select(Post).where(
                Post.status == "scheduled", 
                Post.scheduled_at <= datetime.utcnow()
            )
        )
        return list(result.scalars().all())

    async def update_post_status(self, post_id: int, status: str):
        await self.session.execute(
            update(Post).where(Post.id == post_id).values(status=status)
        )
        await self.session.commit()
