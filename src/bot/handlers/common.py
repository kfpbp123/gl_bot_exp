import telebot
import os
import pytz
import time
from datetime import datetime, timedelta
import html
from src.core import database, ai
from src.bot import keyboards, scheduler
from src.utils import helpers
from src.utils.localizer import t
import config

def register_handlers(bot: telebot.TeleBot):
    from src.bot.handlers.user import user_drafts, user_personas, show_queue_page, show_watermark_menu, send_draft_preview, get_active_channel

    @bot.message_handler(commands=['start', 'restart'])
    def send_welcome(message):
        user_id = message.from_user.id
        user = database.get_user(user_id)
        
        if not user:
            database.add_user(user_id, message.from_user.first_name or "User")
            markup = telebot.types.InlineKeyboardMarkup()
            markup.add(
                telebot.types.InlineKeyboardButton("🇺🇿 O'zbekcha", callback_data="first_lang_uz"),
                telebot.types.InlineKeyboardButton("🇷🇺 Русский", callback_data="first_lang_ru")
            )
            markup.add(telebot.types.InlineKeyboardButton("🇬🇧 English", callback_data="first_lang_en"))
            bot.send_message(message.chat.id, "🌆 Xush kelibsiz! Tilni tanlang:\n\nДобро пожаловать! Выберите язык:\n\nWelcome! Choose language:", reply_markup=markup)
            return

        lang = user[5] if len(user) > 5 else 'uz'
        ensure_user_dir(user_id)
        greeting = helpers.get_time_greeting()
        bot.send_message(message.chat.id, f"{greeting}, {user[1]}!\n\n{t('welcome', lang)}", reply_markup=keyboards.get_main_menu(user_id, lang))

    @bot.message_handler(func=lambda m: m.text in [t('btn_tariffs', 'uz'), t('btn_tariffs', 'ru'), t('btn_tariffs', 'en')])
    def show_tariffs(message):
        user = database.get_user(message.from_user.id)
        lang = user[5] if user and len(user) > 5 else 'uz'
        bot.send_message(message.chat.id, t('tariffs_desc', lang), parse_mode='HTML')

    @bot.callback_query_handler(func=lambda call: True)
    def callback_inline(call):
        chat_id = call.message.chat.id
        user_id = call.from_user.id
        target_id = call.message.message_id
        user = database.get_user(user_id)
        lang = user[5] if user and len(user) > 5 else 'uz'

        if call.data.startswith("first_lang_"):
            new_lang = call.data.split("_")[2]
            database.update_user_language(user_id, new_lang)
            bot.answer_callback_query(call.id, f"✅ {new_lang.upper()}")
            bot.edit_message_text(t('welcome', new_lang), chat_id, target_id)
            bot.send_message(chat_id, t('main_menu', new_lang), reply_markup=keyboards.get_main_menu(user_id, new_lang))
            return

        if (call.data == "add_to_smart_q" or call.data == "pub_now") and (not user or not user[2]):
            msg = bot.send_message(chat_id, t('ask_channel', lang))
            bot.register_next_step_handler(msg, process_channel_setup_step, bot)
            bot.answer_callback_query(call.id)
            return

        if call.data == "reset_watermark":
            database.update_user_logo(user_id, None)
            bot.answer_callback_query(call.id, "✅")
            bot.edit_message_text("❌", chat_id, target_id)
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

        draft = user_drafts.get(target_id) or database.get_user_draft(user_id)
        if not draft and not (call.data.startswith("sched_")):
            return bot.answer_callback_query(call.id, "Error", show_alert=True)

        if call.data == "add_to_smart_q":
            last_time = database.get_last_scheduled_time()
            tashkent_tz = pytz.timezone('Asia/Tashkent')
            current_time = int(datetime.now(tashkent_tz).timestamp())
            interval = getattr(config, 'SMART_QUEUE_INTERVAL_HOURS', 2) * 3600
            new_time = max(last_time + interval if last_time else 0, current_time + interval)
            database.add_to_queue(draft['photo'], draft['text'], draft['document'], draft['channel'], new_time, user_id=user_id)
            bot.answer_callback_query(call.id, "✅")
            bot.edit_message_reply_markup(chat_id, target_id, reply_markup=None)
            user_drafts.pop(target_id, None)
            return

        if call.data == "pub_now":
            if scheduler.publish_post_data(bot, -1, draft['photo'], draft['text'], draft['document'], draft['channel']):
                database.record_published_post(draft['photo'], draft['text'], draft['document'], draft['channel'])
                bot.answer_callback_query(call.id, "🚀")
                bot.edit_message_reply_markup(chat_id, target_id, reply_markup=None)
                user_drafts.pop(target_id, None)
            return

        if call.data == "rewrite_menu":
            new_text = ai.rewrite_post(draft['text'], "fun")
            draft['text'] = new_text
            bot.answer_callback_query(call.id, "✨")
            from src.bot.handlers.user import update_draft_inline
            update_draft_inline(bot, chat_id, target_id, draft)
            return

        if call.data == "cancel_action":
            bot.delete_message(chat_id, target_id)
            user_drafts.pop(target_id, None)
            return

        if call.data.startswith("pers_page_"):
            page = int(call.data.split("_")[2])
            from src.bot.handlers.user import show_style_menu
            # Note: We need to use edit_message instead of send_message inside show_style_menu for better UX, 
            # but for now let's just call it.
            bot.delete_message(chat_id, target_id)
            show_style_menu(bot, chat_id, user_id, page=page)
            return

        if call.data.startswith("set_persona_"):
            persona = call.data.split("_")[2]
            user_personas[user_id] = persona
            bot.answer_callback_query(call.id, f"✅ {persona}")
            bot.edit_message_text(f"✅ Persona: <b>{persona}</b>", chat_id, target_id, parse_mode='HTML')
            return

def ensure_user_dir(user_id):
    path = os.path.join(config.USER_DATA_DIR, str(user_id))
    if not os.path.exists(path): os.makedirs(path)
    return path

def process_channel_setup_step(message, bot):
    user_id = message.from_user.id
    user = database.get_user(user_id)
    lang = user[5] if user and len(user) > 5 else 'uz'
    channel = message.text
    if not channel or not channel.startswith('@'):
        msg = bot.send_message(message.chat.id, "❌ @...")
        bot.register_next_step_handler(msg, process_channel_setup_step, bot)
        return
    database.update_user_channel(user_id, channel)
    bot.send_message(message.chat.id, t('done', lang), reply_markup=keyboards.get_main_menu(user_id, lang))
