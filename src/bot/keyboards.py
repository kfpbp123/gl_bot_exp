from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton, WebAppInfo
import config
from src.utils.localizer import t

def get_main_menu(user_id, lang='uz'):
    markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(KeyboardButton(t('btn_create', lang)))
    markup.add(KeyboardButton(t('btn_style', lang)), KeyboardButton(t('btn_channel', lang)))
    markup.add(KeyboardButton(t('btn_watermark', lang)), KeyboardButton(t('btn_stats', lang)))
    markup.add(KeyboardButton(t('btn_queue', lang)), KeyboardButton(t('btn_tariffs', lang)))
    
    # Кнопка Web App (Telegram Web App)
    markup.add(KeyboardButton(t('btn_webapp', lang), web_app=WebAppInfo(url="https://google.com"))) 
    
    if user_id in config.ADMIN_IDS:
        markup.add(KeyboardButton(t('btn_admin', lang)))
    return markup

def get_admin_menu(lang='uz'):
    markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(KeyboardButton("👥 Список пользователей"), KeyboardButton("📈 Общая статистика"))
    markup.add(KeyboardButton("➕ Добавить канал"), KeyboardButton("💰 Реклама"))
    markup.add(KeyboardButton("💾 Бэкап базы"), KeyboardButton("💡 Запросы подписчиков"))
    markup.add(KeyboardButton(t('btn_home', lang)))
    return markup

def get_cancel_markup(lang='uz'):
    markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
    markup.add(KeyboardButton(t('btn_cancel', lang)))
    return markup

def get_draft_markup():
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton(f"🧠 Умная очередь", callback_data="add_to_smart_q")
    )
    markup.add(
        InlineKeyboardButton("🚀 Сейчас", callback_data="pub_now"),
        InlineKeyboardButton("📅 Позже", callback_data="pub_queue_menu")
    )
    markup.add(
        InlineKeyboardButton("✏️ Правка", callback_data="edit_text"),
        InlineKeyboardButton("✨ Переписать", callback_data="rewrite_menu")
    )
    markup.add(
        InlineKeyboardButton("💰 +Реклама", callback_data="add_ad"),
        InlineKeyboardButton("❌ Удалить", callback_data="cancel_action")
    )
    return markup
