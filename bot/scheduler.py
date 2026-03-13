# bot/scheduler.py
import asyncio
from datetime import datetime
from aiogram import Bot, types
from aiogram.types import InputMediaPhoto
from database.session import async_session
from database.repositories import PostRepository
from core.config import settings
from core.logging import logger

async def process_queue(bot: Bot):
    async with async_session() as session:
        post_repo = PostRepository(session)
        posts = await post_repo.get_scheduled_posts()
        
        for post in posts:
            logger.info("publishing_scheduled_post", post_id=post.id)
            # В этой версии берем первый канал из настроек или из поста
            channel = settings.CHANNELS[0] # TODO: использовать post.channel_id если есть
            
            try:
                if post.media_url:
                    if "," in post.media_url:
                        photo_ids = post.media_url.split(",")
                        media = [InputMediaPhoto(media=p_id) for p_id in photo_ids]
                        media[0].caption = post.text
                        media[0].parse_mode = "HTML"
                        await bot.send_media_group(channel, media)
                    else:
                        await bot.send_photo(channel, post.media_url, caption=post.text, parse_mode="HTML")
                else:
                    await bot.send_message(channel, post.text, parse_mode="HTML")
                
                if post.document_id:
                    await bot.send_document(channel, post.document_id)
                
                await post_repo.update_post(post.id, status="posted")
                
                # Уведомляем админов
                for admin_id in settings.ADMIN_IDS:
                    try:
                        await bot.send_message(admin_id, f"✅ <b>Автопостинг:</b> Пост опубликован в {channel}!", parse_mode="HTML")
                    except:
                        pass
            except Exception as e:
                logger.error("publication_failed", post_id=post.id, error=str(e))
                # Если ошибка критическая (неверный file_id), помечаем как ошибку
                if "wrong file identifier" in str(e).lower():
                    await post_repo.update_post(post.id, status="failed")

async def scheduler_loop(bot: Bot):
    while True:
        try:
            await process_queue(bot)
        except Exception as e:
            logger.error("scheduler_error", error=str(e))
        await asyncio.sleep(60) # Проверка каждую минуту
