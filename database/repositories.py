# database/repositories.py
from sqlalchemy import select, update, delete, func, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.postgresql import insert
from database.models import User, Channel, Post, Comment
from core.logging import logger
from datetime import datetime, timedelta

class BaseRepository:
    def __init__(self, session: AsyncSession):
        self.session = session
        self._logger = logger.bind(repository=self.__class__.__name__)

class UserRepository(BaseRepository):
    async def get_user(self, user_id: int) -> User | None:
        result = await self.session.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    async def upsert_user(self, user_id: int, username: str | None = None, language: str = "ru"):
        """Создает или обновляет пользователя"""
        # Сначала проверяем существование
        user = await self.get_user(user_id)
        if not user:
            user = User(id=user_id, username=username, language=language)
            self.session.add(user)
        else:
            if username: user.username = username
            if language: user.language = language
        
        await self.session.commit()
        return user

class PostRepository(BaseRepository):
    async def create_post(self, user_id: int, text: str, media_url: str | None = None, document_id: str | None = None, channel_id: int | None = None) -> Post:
        post = Post(user_id=user_id, text=text, media_url=media_url, document_id=document_id, channel_id=channel_id, status="draft")
        self.session.add(post)
        await self.session.commit()
        await self.session.refresh(post)
        return post

    async def get_post(self, post_id: int) -> Post | None:
        result = await self.session.execute(select(Post).where(Post.id == post_id))
        return result.scalar_one_or_none()

    async def update_post(self, post_id: int, **kwargs):
        await self.session.execute(
            update(Post).where(Post.id == post_id).values(**kwargs)
        )
        await self.session.commit()

    async def delete_post(self, post_id: int):
        await self.session.execute(delete(Post).where(Post.id == post_id))
        await self.session.commit()

    async def get_scheduled_posts(self) -> list[Post]:
        """Возвращает посты, время публикации которых пришло"""
        result = await self.session.execute(
            select(Post).where(
                Post.status == "scheduled", 
                Post.scheduled_at <= datetime.utcnow()
            )
        )
        return list(result.scalars().all())

    async def get_all_pending(self) -> list[Post]:
        result = await self.session.execute(
            select(Post).where(Post.status == "scheduled").order_by(Post.scheduled_at)
        )
        return list(result.scalars().all())

    async def get_last_scheduled_time(self) -> datetime | None:
        result = await self.session.execute(
            select(Post.scheduled_at)
            .where(Post.status == "scheduled", Post.scheduled_at != None)
            .order_by(desc(Post.scheduled_at))
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def get_stats(self):
        total = await self.session.scalar(select(func.count(Post.id)))
        published = await self.session.scalar(select(func.count(Post.id)).where(Post.status == "posted"))
        queue = await self.session.scalar(select(func.count(Post.id)).where(Post.status == "scheduled"))
        
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        today = await self.session.scalar(
            select(func.count(Post.id)).where(Post.status == "posted", Post.created_at >= today_start)
        )
        
        return {
            "total": total or 0,
            "published": published or 0,
            "queue": queue or 0,
            "today": today or 0
        }

class ChannelRepository(BaseRepository):
    async def get_channels(self) -> list[Channel]:
        result = await self.session.execute(select(Channel))
        return list(result.scalars().all())

    async def add_channel(self, title: str, owner_id: int):
        # В этой архитектуре ID канала (BigInteger) обычно берется из Telegram
        # Но для простоты пока будем использовать title как уникальный идентификатор если нет ID
        channel = Channel(title=title, owner_id=owner_id)
        self.session.add(channel)
        await self.session.commit()
        return channel

class CommentRepository(BaseRepository):
    async def save_comment(self, user_name: str | None, text: str):
        comment = Comment(user_name=user_name, text=text)
        self.session.add(comment)
        await self.session.commit()

    async def get_all_comments(self) -> list[Comment]:
        result = await self.session.execute(select(Comment).order_by(Comment.created_at))
        return list(result.scalars().all())

    async def clear_comments(self):
        await self.session.execute(delete(Comment))
        await self.session.commit()
