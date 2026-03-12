import telebot
import os
import threading
import time
import re
from src.core import database, ai, watermark
from src.bot import keyboards, scheduler
from src.utils import helpers
import config

user_drafts = {}
user_personas = {}
album_cache = {}

def register_user_handlers(bot: telebot.TeleBot):
    @bot.message_handler(func=lambda m: m.text == "📝 Создать пост")
    def create_post_cmd(message):
        bot.send_message(message.chat.id, "Отправь мне фото, текст или ссылку! 🚀")

    @bot.message_handler(func=lambda m: m.text == "🖼️ Мой вотермарк")
    def watermark_menu(message):
        show_watermark_menu(bot, message.chat.id, message.from_user.id)

    @bot.message_handler(func=lambda m: m.text == "📈 Моя статистика")
    def user_stats(message):
        stats = database.get_user_stats(message.from_user.id)
        text = f"📈 <b>ВАША СТАТИСТИКА</b>\n\n📝 Всего: {stats['total']}\n✅ Опубликовано: {stats['published']}\n⏳ В очереди: {stats['queue']}"
        bot.send_message(message.chat.id, text, parse_mode='HTML')

    @bot.message_handler(func=lambda m: m.text == "📊 Статус очереди")
    def queue_status(message):
        show_queue_page(bot, message.chat.id, 0)

    @bot.message_handler(func=lambda m: m.text == "🏠 Главное меню")
    def back_to_main(message):
        bot.send_message(message.chat.id, "🏠 Главное меню", reply_markup=keyboards.get_main_menu(message.from_user.id))

    @bot.message_handler(content_types=['photo', 'text', 'document'])
    def handle_media(message):
        user_id = message.from_user.id
        if not database.get_user(user_id):
            return 

        # Обработка документа (мода) через Reply
        if message.content_type == 'document':
            if message.reply_to_message:
                target_id = message.reply_to_message.message_id
                if target_id in user_drafts:
                    user_drafts[target_id]['document'] = message.document.file_id
                    bot.reply_to(message, "✅ <b>Файл прикреплен к посту!</b> Теперь нажми 'Опубликовать'.", parse_mode='HTML')
                    return
            
            # Если это не реплай, возможно пользователь просто хочет вотермарк (если это PNG)
            if message.document.mime_type == 'image/png':
                show_watermark_menu(bot, message.chat.id, user_id)
                return
            else:
                bot.send_message(message.chat.id, "Чтобы прикрепить файл к посту, отправь его <b>ответом (Reply)</b> на превью поста.", parse_mode='HTML')
                return

        if message.media_group_id:
            if message.media_group_id not in album_cache:
                album_cache[message.media_group_id] = []
                bot.send_message(message.chat.id, "📸 Загружаю альбом...")
                threading.Timer(2.0, process_album, args=[bot, message.media_group_id, message.chat.id, user_id]).start()
            album_cache[message.media_group_id].append(message)
            return
        
        if message.content_type == 'text' and message.text in ["📝 Создать пост", "🖼️ Мой вотермарк", "📈 Моя статистика", "📊 Статус очереди", "🛡️ Админ-панель", "🏠 Главное меню", "❌ Отмена"]:
            return 

        process_single_message(bot, message)

def process_single_message(bot, message):
    user_id = message.from_user.id
    user_dir = os.path.join(config.USER_DATA_DIR, str(user_id))
    if not os.path.exists(user_dir): os.makedirs(user_dir)
    
    temp_in = os.path.join(user_dir, f"in_{message.message_id}.jpg")
    temp_out = os.path.join(user_dir, f"out_{message.message_id}.jpg")
    
    try:
        user_input = message.caption if message.photo else message.text
        if not user_input: return
        
        persona = user_personas.get(user_id, "uz")
        generated_text = ai.generate_post(user_input, persona)
        photo_id = None
        
        if message.photo:
            bot.send_message(message.chat.id, "🎨 Обрабатываю...")
            file_info = bot.get_file(message.photo[-1].file_id)
            downloaded_file = bot.download_file(file_info.file_path)
            with open(temp_in, 'wb') as f: f.write(downloaded_file)
            
            user = database.get_user(user_id)
            watermark.add_watermark(temp_in, temp_out, user[3] if user else None)
            
            target = temp_out if os.path.exists(temp_out) else temp_in
            with open(target, 'rb') as f:
                sent = bot.send_photo(message.chat.id, f)
                photo_id = sent.photo[-1].file_id
                try: bot.delete_message(message.chat.id, sent.message_id)
                except: pass
        
        draft = {'photo': photo_id, 'text': generated_text, 'document': None, 'ad_added': False, 'channel': get_active_channel(user_id)}
        # Сохраняем в БД, чтобы не потерять при перезагрузке
        database.save_user_draft(user_id, draft['photo'], draft['text'], draft['document'], draft['channel'])
        send_draft_preview(bot, message.chat.id, draft)
    except Exception as e:
        bot.send_message(message.chat.id, f"Ошибка: {e}")
    finally:
        for f in [temp_in, temp_out]:
            if os.path.exists(f):
                try: os.remove(f)
                except: pass

def process_album(bot, media_group_id, chat_id, user_id):
    messages = album_cache.pop(media_group_id, None)
    if not messages: return
    messages.sort(key=lambda x: x.message_id)
    caption = next((m.caption for m in messages if m.caption), "Опиши мод")
    
    user_dir = os.path.join(config.USER_DATA_DIR, str(user_id))
    temp_files = []
    opened_files = []
    
    try:
        user = database.get_user(user_id)
        logo = user[3] if user else None
        
        for i, m in enumerate(messages):
            file_info = bot.get_file(m.photo[-1].file_id)
            downloaded = bot.download_file(file_info.file_path)
            tin, tout = os.path.join(user_dir, f"in_{i}.jpg"), os.path.join(user_dir, f"out_{i}.jpg")
            with open(tin, 'wb') as f: f.write(downloaded)
            watermark.add_watermark(tin, tout, logo)
            temp_files.append((tin, tout if os.path.exists(tout) else tin))
            
        media = []
        for tin, target_img in temp_files:
            f = open(target_img, 'rb')
            opened_files.append(f)
            media.append(telebot.types.InputMediaPhoto(f))
            
        sent_msgs = bot.send_media_group(chat_id, media)
        photo_ids = [m.photo[-1].file_id for m in sent_msgs]
        photo_id_str = ",".join(photo_ids)
        
        for m in sent_msgs:
            try: bot.delete_message(chat_id, m.message_id)
            except: pass
            
        draft = {'photo': photo_id_str, 'text': ai.generate_post(caption, user_personas.get(user_id, "uz")), 
                 'document': None, 'ad_added': False, 'channel': get_active_channel(user_id)}
        
        # Сохраняем в БД
        database.save_user_draft(user_id, draft['photo'], draft['text'], draft['document'], draft['channel'])
        send_draft_preview(bot, chat_id, draft)
    except Exception as e:
        bot.send_message(chat_id, f"Ошибка альбома: {e}")
    finally:
        for f in opened_files: f.close()
        for tin, tout in temp_files:
            if os.path.exists(tin): os.remove(tin)
            if os.path.exists(tout) and tout != tin: os.remove(tout)

def send_draft_preview(bot, chat_id, draft):
    text = draft['text']
    photo_id = draft['photo']
    target_id = None

    try:
        if photo_id:
            if ',' in photo_id:
                ids = photo_id.split(',')
                media = [telebot.types.InputMediaPhoto(media=pid) for pid in ids]
                bot.send_media_group(chat_id, media)
                sent = bot.send_message(chat_id, text, parse_mode='HTML')
                target_id = sent.message_id
            else:
                if len(text) <= 1024:
                    sent = bot.send_photo(chat_id, photo_id, caption=text, parse_mode='HTML')
                    target_id = sent.message_id
                else:
                    bot.send_photo(chat_id, photo_id)
                    sent = bot.send_message(chat_id, text, parse_mode='HTML')
                    target_id = sent.message_id
        else:
            sent = bot.send_message(chat_id, text, parse_mode='HTML')
            target_id = sent.message_id
            
        user_drafts[target_id] = draft
        # Также связываем user_id с target_id в памяти для быстрого доступа
        user_id = None
        for uid, d in database.get_all_users(): # Это просто пример, на самом деле мы знаем user_id из контекста вызова
            pass 

        bot.edit_message_reply_markup(chat_id, target_id, reply_markup=keyboards.get_draft_markup())
    except Exception as e:
        bot.send_message(chat_id, f"❌ Ошибка превью: {e}")

def update_draft_inline(bot, chat_id, target_id, draft):
    markup = keyboards.get_draft_markup()
    try:
        bot.edit_message_text(text=draft['text'], chat_id=chat_id, message_id=target_id, parse_mode='HTML', reply_markup=markup)
    except:
        try:
            bot.edit_message_caption(caption=draft['text'], chat_id=chat_id, message_id=target_id, parse_mode='HTML', reply_markup=markup)
        except: pass

def get_active_channel(user_id):
    u = database.get_user(user_id)
    return u[2] if u and u[2] else config.DEFAULT_CHANNEL

def show_watermark_menu(bot, chat_id, user_id):
    user = database.get_user(user_id)
    status = "✅ Установлен" if user and user[3] else "❌ Не установлен"
    text = f"🖼️ <b>МОЙ ВОТЕРМАРК</b>\n\nСтатус: {status}\n\nПришли PNG-файл как ДОКУМЕНТ."
    markup = telebot.types.InlineKeyboardMarkup()
    if user and user[3]:
        markup.add(telebot.types.InlineKeyboardButton("🗑 Сбросить", callback_data="reset_watermark"))
    msg = bot.send_message(chat_id, text, parse_mode='HTML', reply_markup=markup)
    bot.register_next_step_handler(msg, process_watermark_step, bot)

def process_watermark_step(message, bot):
    user_id = message.from_user.id
    if message.text in ["❌ Отмена", "🏠 Главное меню"]:
        bot.send_message(message.chat.id, "🏠 Главное меню", reply_markup=keyboards.get_main_menu(user_id))
        return

    if not message.document:
        msg = bot.send_message(message.chat.id, "❌ Пожалуйста, отправь PNG как ДОКУМЕНТ:")
        bot.register_next_step_handler(msg, process_watermark_step, bot)
        return

    user_dir = os.path.join(config.USER_DATA_DIR, str(user_id))
    if not os.path.exists(user_dir): os.makedirs(user_dir)
    logo_path = os.path.join(user_dir, "custom_logo.png")
    
    file_info = bot.get_file(message.document.file_id)
    downloaded = bot.download_file(file_info.file_path)
    with open(logo_path, 'wb') as f: f.write(downloaded)
    database.update_user_logo(user_id, logo_path)
    bot.send_message(message.chat.id, "✅ Вотермарк сохранен!", reply_markup=keyboards.get_main_menu(user_id))

def show_queue_page(bot, chat_id, page, message_id=None):
    posts = database.get_all_pending()
    if not posts:
        if message_id: bot.edit_message_text("📭 Очередь пуста.", chat_id, message_id)
        else: bot.send_message(chat_id, "📭 Очередь пуста.")
        return

    if page >= len(posts): page = len(posts) - 1
    if page < 0: page = 0

    msg_text = f"🕒 <b>В очереди: {len(posts)} постов</b>\n\n"
    msg_text += helpers.format_queue_post(posts[page], page + 1, len(posts))

    markup = telebot.types.InlineKeyboardMarkup(row_width=2)
    nav_row = []
    if page > 0: nav_row.append(telebot.types.InlineKeyboardButton("⬅️ Пред.", callback_data=f"q_page_{page-1}"))
    if page < len(posts) - 1: nav_row.append(telebot.types.InlineKeyboardButton("След. ➡️", callback_data=f"q_page_{page+1}"))
    if nav_row: markup.add(*nav_row)

    markup.add(
        telebot.types.InlineKeyboardButton("🚀 Выпустить сейчас", callback_data=f"q_pub_{posts[page][0]}"),
        telebot.types.InlineKeyboardButton("🗑 Удалить", callback_data=f"q_del_{posts[page][0]}")
    )

    if message_id:
        try: bot.edit_message_text(msg_text, chat_id, message_id, parse_mode='HTML', reply_markup=markup)
        except: pass
    else:
        bot.send_message(chat_id, msg_text, parse_mode='HTML', reply_markup=markup)
