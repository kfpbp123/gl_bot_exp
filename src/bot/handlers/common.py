import telebot
import os
import pytz
import time
from datetime import datetime, timedelta
import html
from src.core import database, ai
from src.bot import keyboards, scheduler
from src.utils import helpers
import config

def register_handlers(bot: telebot.TeleBot):
    # We need access to user_drafts and other state. 
    # Usually, it's better to import them from user.py or have a shared state module.
    from src.bot.handlers.user import user_drafts, user_personas, show_queue_page, show_watermark_menu, send_draft_preview, get_active_channel

    @bot.message_handler(commands=['start'])
    def send_welcome(message):
        user_id = message.from_user.id
        user = database.get_user(user_id)
        
        if not user:
            msg = bot.send_message(message.chat.id, "👋 Привет! Добро пожаловать.\n\nВведи никнейм для регистрации:")
            bot.register_next_step_handler(msg, process_registration_step, bot)
            return

        ensure_user_dir(user_id)
        greeting = helpers.get_time_greeting()
        bot.send_message(message.chat.id, f"{greeting}, {user[1]}!", reply_markup=keyboards.get_main_menu(user_id))

    @bot.message_handler(func=lambda m: m.text == "💰 Тарифы")
    def show_tariffs(message):
        text = (
            "💰 <b>ТАРИФЫ И ПОДПИСКА</b>\n\n"
            "Выберите подходящий план для автоматизации вашего канала:\n\n"
            "🔹 <b>FREE</b> — 3 поста в день, вотермарк.\n"
            "🔸 <b>PREMIUM</b> — Безлимит, умная очередь, AI-генерация, приоритет.\n"
            "🚀 <b>ULTRA</b> — Управление несколькими каналами + Рекламный модуль.\n\n"
            "<i>Для покупки свяжитесь с администратором.</i>"
        )
        markup = telebot.types.InlineKeyboardMarkup()
        markup.add(telebot.types.InlineKeyboardButton("💳 Купить", url=f"tg://user?id={config.ADMIN_IDS[0]}"))
        bot.send_message(message.chat.id, text, parse_mode='HTML', reply_markup=markup)

    @bot.callback_query_handler(func=lambda call: True)
    def callback_inline(call):
        chat_id = call.message.chat.id
        user_id = call.from_user.id
        target_id = call.message.message_id

        if call.data == "reset_watermark":
            database.update_user_logo(user_id, None)
            bot.answer_callback_query(call.id, "✅ Сброшено!")
            bot.edit_message_text("❌ Личный вотермарк удален.", chat_id, target_id)
            return

        if call.data.startswith("q_page_"):
            page = int(call.data.split('_')[2])
            show_queue_page(bot, chat_id, page, message_id=target_id)
            return

        if call.data.startswith("q_pub_"):
            post_id = int(call.data.split('_')[2])
            posts = database.get_all_pending()
            post = next((p for p in posts if p[0] == post_id), None)
            if post and scheduler.publish_post_data(bot, post[0], post[1], post[2], post[3], post[4]):
                bot.answer_callback_query(call.id, "🚀")
                show_queue_page(bot, chat_id, 0, message_id=target_id)
            return

        if call.data.startswith("q_del_"):
            database.delete_from_queue(int(call.data.split('_')[2]))
            show_queue_page(bot, chat_id, 0, message_id=target_id)
            return

        draft = user_drafts.get(target_id)
        if not draft and not (call.data.startswith("sched_")):
            return bot.answer_callback_query(call.id, "Черновик устарел.", show_alert=True)

        if call.data == "add_to_smart_q":
            last_time = database.get_last_scheduled_time()
            tashkent_tz = pytz.timezone('Asia/Tashkent')
            current_time = int(datetime.now(tashkent_tz).timestamp())
            interval = getattr(config, 'SMART_QUEUE_INTERVAL_HOURS', 2) * 3600
            new_time = max(last_time + interval if last_time else 0, current_time + interval)
            
            database.add_to_queue(draft['photo'], draft['text'], draft['document'], draft['channel'], new_time, user_id=user_id)
            dt_str = datetime.fromtimestamp(new_time, tashkent_tz).strftime('%d.%m.%Y %H:%M')
            bot.answer_callback_query(call.id, "✅ Добавлено!")
            bot.edit_message_reply_markup(chat_id, target_id, reply_markup=None)
            bot.send_message(chat_id, f"🧠 Запланировано на {dt_str}", parse_mode="HTML")
            user_drafts.pop(target_id, None)
            return

        if call.data == "pub_now":
            if scheduler.publish_post_data(bot, -1, draft['photo'], draft['text'], draft['document'], draft['channel']):
                database.record_published_post(draft['photo'], draft['text'], draft['document'], draft['channel'])
                bot.answer_callback_query(call.id, "🚀")
                bot.edit_message_reply_markup(chat_id, target_id, reply_markup=None)
                user_drafts.pop(target_id, None)
            return

        if call.data == "edit_text":
            msg = bot.send_message(chat_id, "✏️ Введи новый текст:", reply_markup=keyboards.get_cancel_markup())
            bot.register_next_step_handler(msg, process_edit_text, bot, target_id)
            return

        if call.data == "rewrite_menu":
            # Simplified rewrite menu
            new_text = ai.rewrite_post(draft['text'], "fun")
            draft['text'] = new_text
            bot.answer_callback_query(call.id, "✨ Переписано!")
            from src.bot.handlers.user import update_draft_inline
            update_draft_inline(bot, chat_id, target_id, draft)
            return

        if call.data == "cancel_action":
            bot.delete_message(chat_id, target_id)
            user_drafts.pop(target_id, None)
            bot.answer_callback_query(call.id, "Удалено")
            return

def ensure_user_dir(user_id):
    path = os.path.join(config.USER_DATA_DIR, str(user_id))
    if not os.path.exists(path):
        os.makedirs(path)
    return path

def process_registration_step(message, bot):
    user_id = message.from_user.id
    username = message.text
    if not username or len(username) < 2:
        msg = bot.send_message(message.chat.id, "❌ Слишком коротко. Еще раз:")
        bot.register_next_step_handler(msg, process_registration_step, bot)
        return
    database.add_user(user_id, username)
    ensure_user_dir(user_id)
    msg = bot.send_message(message.chat.id, f"✅ Привет, {username}! Пришли @username твоего канала:")
    bot.register_next_step_handler(msg, process_channel_setup_step, bot)

def process_channel_setup_step(message, bot):
    user_id = message.from_user.id
    channel = message.text
    if not channel or not channel.startswith('@'):
        msg = bot.send_message(message.chat.id, "❌ Начни с @. Еще раз:")
        bot.register_next_step_handler(msg, process_channel_setup_step, bot)
        return
    database.update_user_channel(user_id, channel)
    bot.send_message(message.chat.id, "✅ Готово!", reply_markup=keyboards.get_main_menu(user_id))

def process_edit_text(message, bot, target_id):
    from src.bot.handlers.user import user_drafts, send_draft_preview
    if message.text == "❌ Отмена":
        bot.send_message(message.chat.id, "Отменено.")
        return
    draft = user_drafts.pop(target_id, None)
    if not draft: return
    draft['text'] = message.text
    try: bot.delete_message(message.chat.id, target_id)
    except: pass
    send_draft_preview(bot, message.chat.id, draft)
