import telebot
import os
import threading
import time
import re
from src.core import database, ai, watermark
from src.bot import keyboards, scheduler
from src.utils import helpers
from src.utils.localizer import t
import config

user_drafts = {}
user_personas = {}
album_cache = {}

def register_user_handlers(bot: telebot.TeleBot):
    @bot.message_handler(func=lambda m: m.text in [t('btn_create', 'uz'), t('btn_create', 'ru'), t('btn_create', 'en')])
    def create_post_cmd(message):
        user = database.get_user(message.from_user.id)
        lang = user[5] if user and len(user) > 5 else 'uz'
        bot.send_message(message.chat.id, "Отправь мне фото, текст или ссылку! 🚀")

    @bot.message_handler(func=lambda m: m.text in [t('btn_watermark', 'uz'), t('btn_watermark', 'ru'), t('btn_watermark', 'en')])
    def watermark_menu(message):
        show_watermark_menu(bot, message.chat.id, message.from_user.id)

    @bot.message_handler(func=lambda m: m.text in [t('btn_stats', 'uz'), t('btn_stats', 'ru'), t('btn_stats', 'en')])
    def user_stats(message):
        user = database.get_user(message.from_user.id)
        lang = user[5] if user and len(user) > 5 else 'uz'
        stats = database.get_user_stats(message.from_user.id)
        text = f"📈 <b>{t('btn_stats', lang).upper()}</b>\n\n📝 Всего: {stats['total']}\n✅ Опубликовано: {stats['published']}\n⏳ В очереди: {stats['queue']}"
        bot.send_message(message.chat.id, text, parse_mode='HTML')

    @bot.message_handler(func=lambda m: m.text in [t('btn_queue', 'uz'), t('btn_queue', 'ru'), t('btn_queue', 'en')])
    def queue_status(message):
        show_queue_page(bot, message.chat.id, 0)

    @bot.message_handler(func=lambda m: m.text in [t('btn_style', 'uz'), t('btn_style', 'ru'), t('btn_style', 'en')])
    def style_menu_cmd(message):
        show_style_menu(bot, message.chat.id, message.from_user.id)

    @bot.message_handler(func=lambda m: m.text in [t('btn_channel', 'uz'), t('btn_channel', 'ru'), t('btn_channel', 'en')])
    def channel_menu(message):
        user = database.get_user(message.from_user.id)
        lang = user[5] if user and len(user) > 5 else 'uz'
        current = user[2] if user and user[2] else "N/A"
        text = f"📢 <b>{t('btn_channel', lang)}</b>\n\nТекущий: <code>{current}</code>\n\nПришли @username нового канала:"
        msg = bot.send_message(message.chat.id, text, parse_mode='HTML', reply_markup=keyboards.get_cancel_markup(lang))
        from src.bot.handlers.common import process_channel_setup_step
        bot.register_next_step_handler(msg, process_channel_setup_step, bot)

    @bot.message_handler(func=lambda m: m.text in [t('btn_home', 'uz'), t('btn_home', 'ru'), t('btn_home', 'en')])
    def back_to_main(message):
        user = database.get_user(message.from_user.id)
        lang = user[5] if user and len(user) > 5 else 'uz'
        bot.send_message(message.chat.id, t('main_menu', lang), reply_markup=keyboards.get_main_menu(message.from_user.id, lang))

    @bot.message_handler(content_types=['photo', 'text', 'document'])
    def handle_media(message):
        user_id = message.from_user.id
        user = database.get_user(user_id)
        if not user: return 
        lang = user[5] if len(user) > 5 else 'uz'

        if message.content_type == 'document':
            if message.reply_to_message:
                target_id = message.reply_to_message.message_id
                draft = user_drafts.get(target_id) or database.get_user_draft(user_id)
                if draft:
                    draft['document'] = message.document.file_id
                    user_drafts[target_id] = draft
                    database.save_user_draft(user_id, draft['photo'], draft['text'], draft['document'], draft['channel'])
                    bot.reply_to(message, "✅ File attached!")
                    return
            
            if message.document.mime_type == 'image/png':
                show_watermark_menu(bot, message.chat.id, user_id)
                return

        if message.media_group_id:
            if message.media_group_id not in album_cache:
                album_cache[message.media_group_id] = []
                threading.Timer(2.0, process_album, args=[bot, message.media_group_id, message.chat.id, user_id]).start()
            album_cache[message.media_group_id].append(message)
            return
        
        if message.content_type == 'text' and any(message.text == t(k, l) for k in ['btn_create', 'btn_style', 'btn_channel', 'btn_watermark', 'btn_stats', 'btn_queue', 'btn_tariffs', 'btn_admin', 'btn_home'] for l in ['uz', 'ru', 'en']):
            return 

        process_single_message(bot, message)

def show_style_menu(bot, chat_id, user_id, page=0):
    user = database.get_user(user_id)
    lang = user[5] if user and len(user) > 5 else 'uz'
    
    personas = list(ai.PERSONAS[lang].keys())
    per_page = 6
    start = page * per_page
    end = start + per_page
    
    markup = telebot.types.InlineKeyboardMarkup(row_width=2)
    for p_key in personas[start:end]:
        # Получаем короткое название или эмодзи для кнопки (первое слово описания)
        desc = ai.PERSONAS[lang][p_key].split(':')[0]
        markup.add(telebot.types.InlineKeyboardButton(desc, callback_data=f"set_persona_{p_key}"))
    
    nav = []
    if page > 0: nav.append(telebot.types.InlineKeyboardButton("⬅️", callback_data=f"pers_page_{page-1}"))
    if end < len(personas): nav.append(telebot.types.InlineKeyboardButton("➡️", callback_data=f"pers_page_{page+1}"))
    if nav: markup.add(*nav)
    
    current = user_personas.get(user_id, "gamer")
    bot.send_message(chat_id, f"{t('style_desc', lang)}\n\nCurrent: <b>{current}</b>", parse_mode='HTML', reply_markup=markup)

def process_single_message(bot, message):
    user_id = message.from_user.id
    user = database.get_user(user_id)
    lang = user[5] if user and len(user) > 5 else 'uz'
    user_dir = os.path.join(config.USER_DATA_DIR, str(user_id))
    if not os.path.exists(user_dir): os.makedirs(user_dir)
    
    temp_in = os.path.join(user_dir, f"in_{message.message_id}.jpg")
    temp_out = os.path.join(user_dir, f"out_{message.message_id}.jpg")
    
    try:
        user_input = message.caption if message.photo else message.text
        if not user_input: return
        
        persona = user_personas.get(user_id, "gamer")
        generated_text = ai.generate_post(user_input, persona, lang)
        photo_id = None
        
        if message.photo:
            file_info = bot.get_file(message.photo[-1].file_id)
            downloaded = bot.download_file(file_info.file_path)
            with open(temp_in, 'wb') as f: f.write(downloaded)
            watermark.add_watermark(temp_in, temp_out, user[3] if user else None)
            target = temp_out if os.path.exists(temp_out) else temp_in
            with open(target, 'rb') as f:
                sent = bot.send_photo(message.chat.id, f)
                photo_id = sent.photo[-1].file_id
                try: bot.delete_message(message.chat.id, sent.message_id)
                except: pass
        
        draft = {'photo': photo_id, 'text': generated_text, 'document': None, 'ad_added': False, 'channel': get_active_channel(user_id)}
        database.save_user_draft(user_id, draft['photo'], draft['text'], draft['document'], draft['channel'])
        send_draft_preview(bot, message.chat.id, draft)
    except Exception as e:
        bot.send_message(message.chat.id, f"Error: {e}")
    finally:
        for f in [temp_in, temp_out]:
            if os.path.exists(f): os.remove(f)

def process_album(bot, media_group_id, chat_id, user_id):
    messages = album_cache.pop(media_group_id, None)
    if not messages: return
    user = database.get_user(user_id)
    lang = user[5] if user and len(user) > 5 else 'uz'
    messages.sort(key=lambda x: x.message_id)
    caption = next((m.caption for m in messages if m.caption), "Minecraft Mod")
    
    user_dir = os.path.join(config.USER_DATA_DIR, str(user_id))
    temp_files = []
    opened_files = []
    
    try:
        logo = user[3] if user else None
        for i, m in enumerate(messages):
            file_info = bot.get_file(m.photo[-1].file_id)
            downloaded = bot.download_file(file_info.file_path)
            tin, tout = os.path.join(user_dir, f"in_a_{i}.jpg"), os.path.join(user_dir, f"out_a_{i}.jpg")
            with open(tin, 'wb') as f: f.write(downloaded)
            watermark.add_watermark(tin, tout, logo)
            temp_files.append((tin, tout if os.path.exists(tout) else tin))
            
        media = []
        for _, target_img in temp_files:
            f = open(target_img, 'rb')
            opened_files.append(f)
            media.append(telebot.types.InputMediaPhoto(f))
            
        sent_msgs = bot.send_media_group(chat_id, media)
        photo_id_str = ",".join([m.photo[-1].file_id for m in sent_msgs])
        for m in sent_msgs:
            try: bot.delete_message(chat_id, m.message_id)
            except: pass
            
        persona = user_personas.get(user_id, "gamer")
        draft = {'photo': photo_id_str, 'text': ai.generate_post(caption, persona, lang), 
                 'document': None, 'ad_added': False, 'channel': get_active_channel(user_id)}
        database.save_user_draft(user_id, draft['photo'], draft['text'], draft['document'], draft['channel'])
        send_draft_preview(bot, chat_id, draft)
    except Exception as e:
        bot.send_message(chat_id, f"Album error: {e}")
    finally:
        for f in opened_files: f.close()
        for tin, tout in temp_files:
            if os.path.exists(tin): os.remove(tin)
            if os.path.exists(tout) and tout != tin: os.remove(tout)

def send_draft_preview(bot, chat_id, draft):
    text, photo_id = draft['text'], draft['photo']
    try:
        if photo_id:
            if ',' in photo_id:
                media = [telebot.types.InputMediaPhoto(media=pid) for pid in photo_id.split(',')]
                bot.send_media_group(chat_id, media)
                sent = bot.send_message(chat_id, text, parse_mode='HTML')
            else:
                sent = bot.send_photo(chat_id, photo_id, caption=text[:1024], parse_mode='HTML')
            target_id = sent.message_id
        else:
            sent = bot.send_message(chat_id, text, parse_mode='HTML')
            target_id = sent.message_id
            
        user_drafts[target_id] = draft
        bot.edit_message_reply_markup(chat_id, target_id, reply_markup=keyboards.get_draft_markup())
    except Exception as e:
        bot.send_message(chat_id, f"Preview error: {e}")

def update_draft_inline(bot, chat_id, target_id, draft):
    markup = keyboards.get_draft_markup()
    try:
        bot.edit_message_text(text=draft['text'], chat_id=chat_id, message_id=target_id, parse_mode='HTML', reply_markup=markup)
    except:
        try: bot.edit_message_caption(caption=draft['text'], chat_id=chat_id, message_id=target_id, parse_mode='HTML', reply_markup=markup)
        except: pass

def get_active_channel(user_id):
    u = database.get_user(user_id)
    return u[2] if u and u[2] else config.DEFAULT_CHANNEL

def show_watermark_menu(bot, chat_id, user_id):
    user = database.get_user(user_id)
    lang = user[5] if user and len(user) > 5 else 'uz'
    status = "✅" if user and user[3] else "❌"
    text = f"🖼️ <b>{t('btn_watermark', lang)}</b>\n\nStatus: {status}\n\nSend PNG as DOCUMENT."
    markup = telebot.types.InlineKeyboardMarkup()
    if user and user[3]: markup.add(telebot.types.InlineKeyboardButton("🗑 Reset", callback_data="reset_watermark"))
    msg = bot.send_message(chat_id, text, parse_mode='HTML', reply_markup=markup)
    bot.register_next_step_handler(msg, process_watermark_step, bot)

def process_watermark_step(message, bot):
    user_id = message.from_user.id
    user = database.get_user(user_id)
    lang = user[5] if user and len(user) > 5 else 'uz'
    
    # Check if user clicked a menu button to exit
    if message.text:
        # Check against all possible translations of main menu buttons
        all_btns = []
        for l in ['uz', 'ru', 'en']:
            all_btns.extend([t(k, l) for k in ['btn_create', 'btn_style', 'btn_channel', 'btn_watermark', 'btn_stats', 'btn_queue', 'btn_tariffs', 'btn_admin', 'btn_home', 'btn_cancel']])
        
        if message.text in all_btns:
            bot.send_message(message.chat.id, t('main_menu', lang), reply_markup=keyboards.get_main_menu(user_id, lang))
            return

    if not message.document or message.document.mime_type != 'image/png':
        msg = bot.send_message(message.chat.id, "❌ Send PNG DOCUMENT:")
        bot.register_next_step_handler(msg, process_watermark_step, bot)
        return

    user_dir = os.path.join(config.USER_DATA_DIR, str(user_id))
    if not os.path.exists(user_dir): os.makedirs(user_dir)
    logo_path = os.path.join(user_dir, "custom_logo.png")
    
    file_info = bot.get_file(message.document.file_id)
    downloaded = bot.download_file(file_info.file_path)
    with open(logo_path, 'wb') as f: f.write(downloaded)
    database.update_user_logo(user_id, logo_path)
    bot.send_message(message.chat.id, "✅ Saved!", reply_markup=keyboards.get_main_menu(user_id, lang))

def show_queue_page(bot, chat_id, page, message_id=None):
    user = database.get_user(chat_id)
    lang = user[5] if user and len(user) > 5 else 'uz'
    posts = database.get_all_pending()
    if not posts:
        if message_id: bot.edit_message_text("📭 Empty", chat_id, message_id)
        else: bot.send_message(chat_id, "📭 Empty")
        return

    if page >= len(posts): page = len(posts) - 1
    if page < 0: page = 0

    msg_text = f"🕒 <b>Queue: {len(posts)}</b>\n\n" + helpers.format_queue_post(posts[page], page + 1, len(posts))
    markup = telebot.types.InlineKeyboardMarkup(row_width=2)
    nav = []
    if page > 0: nav.append(telebot.types.InlineKeyboardButton("⬅️", callback_data=f"q_page_{page-1}"))
    if page < len(posts) - 1: nav.append(telebot.types.InlineKeyboardButton("➡️", callback_data=f"q_page_{page+1}"))
    if nav: markup.add(*nav)
    markup.add(telebot.types.InlineKeyboardButton("🚀 Pub", callback_data=f"q_pub_{posts[page][0]}"),
               telebot.types.InlineKeyboardButton("🗑 Del", callback_data=f"q_del_{posts[page][0]}"))

    if message_id:
        try: bot.edit_message_text(msg_text, chat_id, message_id, parse_mode='HTML', reply_markup=markup)
        except: pass
    else: bot.send_message(chat_id, msg_text, parse_mode='HTML', reply_markup=markup)
