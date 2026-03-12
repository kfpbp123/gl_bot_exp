from apscheduler.schedulers.background import BackgroundScheduler
import telebot
import config
from src.core import database
import os

def init_scheduler(bot: telebot.TeleBot):
    scheduler = BackgroundScheduler()
    scheduler.add_job(process_queue, 'interval', minutes=1, args=[bot])
    scheduler.start()
    return scheduler

def process_queue(bot: telebot.TeleBot):
    posts = database.get_ready_posts()
    for post in posts:
        post_id, photo_id, text, document_id, channel_id = post
        target_channel = channel_id if channel_id else config.DEFAULT_CHANNEL
        publish_post_data(bot, post_id, photo_id, text, document_id, target_channel, is_auto=True)

def publish_post_data(bot: telebot.TeleBot, post_id, photo_id, text, document_id, channel_id, is_auto=False):
    print(f"🚀 Попытка публикации поста {post_id} в {channel_id}...")
    try:
        if photo_id:
            if ',' in photo_id:
                ids = photo_id.split(',')
                print(f"  - Отправка альбома из {len(ids)} фото")
                media = [telebot.types.InputMediaPhoto(media=pid, caption=text if i==0 and len(text)<=1024 else None, parse_mode='HTML') for i, pid in enumerate(ids)]
                bot.send_media_group(channel_id, media)
                if len(text) > 1024:
                    bot.send_message(channel_id, text, parse_mode='HTML')
            else:
                print(f"  - Отправка одиночного фото: {photo_id}")
                if len(text) <= 1024:
                    bot.send_photo(channel_id, photo_id, caption=text, parse_mode='HTML')
                else:
                    bot.send_photo(channel_id, photo_id)
                    bot.send_message(channel_id, text, parse_mode='HTML')
        else:
            print("  - Отправка текстового сообщения")
            bot.send_message(channel_id, text, parse_mode='HTML')
            
        if document_id: 
            print(f"  - Отправка документа: {document_id}")
            bot.send_document(channel_id, document_id)
        
        if post_id != -1: 
            database.mark_as_posted(post_id)
            if is_auto:
                for admin in config.ADMIN_IDS:
                    try: bot.send_message(admin, f"✅ <b>Автопостинг:</b> Пост опубликован в {channel_id}!", parse_mode='HTML')
                    except: pass
                    
        print(f"✅ Пост {post_id} успешно опубликован!")
        return True
    except Exception as e:
        print(f"❌ Ошибка при публикации поста {post_id}: {e}")
        
        # Если ошибка в неверном ID файла, помечаем пост как 'failed', чтобы не пытаться вечно
        if "wrong file identifier" in str(e).lower() or "file_id" in str(e).lower():
            print(f"⚠️ Пост {post_id} имеет неверный ID файла. Помечаем как пропущенный.")
            if post_id != -1:
                database.mark_as_posted(post_id) # Или добавить mark_as_failed в базу
        
        if post_id != -1 and is_auto:
            for admin in config.ADMIN_IDS:
                try: bot.send_message(admin, f"❌ <b>Ошибка публикации {post_id}:</b> {e}", parse_mode='HTML')
                except: pass
        return False
