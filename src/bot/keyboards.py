from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
import config

def get_main_menu(user_id):
    markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(KeyboardButton("📝 Создать пост"))
    markup.add(KeyboardButton("🎭 Выбор стиля"), KeyboardButton("📢 Выбор канала"))
    markup.add(KeyboardButton("🖼️ Мой вотермарк"), KeyboardButton("📈 Моя статистика"))
    markup.add(KeyboardButton("📊 Статус очереди"))
    
    if user_id in config.ADMIN_IDS:
        markup.add(KeyboardButton("🛡️ Админ-панель"))
    return markup

def get_admin_menu():
    markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(KeyboardButton("👥 Список пользователей"), KeyboardButton("📈 Общая статистика"))
    markup.add(KeyboardButton("➕ Добавить канал"), KeyboardButton("💰 Реклама"))
    markup.add(KeyboardButton("💾 Бэкап базы"), KeyboardButton("💡 Запросы подписчиков"))
    markup.add(KeyboardButton("🏠 Главное меню"))
    return markup

def get_cancel_markup():
    markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
    markup.add(KeyboardButton("❌ Отмена"))
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
