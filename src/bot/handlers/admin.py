import telebot
from src.core import database
from src.bot import keyboards
from src.utils import analyzer
import config
import os

def register_admin_handlers(bot: telebot.TeleBot):
    @bot.message_handler(func=lambda m: m.text == "🛡️ Админ-панель" and m.from_user.id in config.ADMIN_IDS)
    def admin_panel(message):
        bot.send_message(message.chat.id, "🛡️ Панель администратора", reply_markup=keyboards.get_admin_menu())

    @bot.message_handler(func=lambda m: m.text == "👥 Список пользователей" and m.from_user.id in config.ADMIN_IDS)
    def list_users(message):
        users = database.get_all_users()
        text = "👥 <b>Пользователи:</b>\n\n"
        for u in users:
            text += f"👤 {u[1]} (ID: {u[0]})\n📢 {u[2] or 'N/A'}\n\n"
        bot.send_message(message.chat.id, text, parse_mode='HTML')

    @bot.message_handler(func=lambda m: m.text == "📈 Общая статистика" and m.from_user.id in config.ADMIN_IDS)
    def global_stats(message):
        stats = database.get_admin_stats()
        text = f"📊 <b>ОБЩАЯ СТАТИСТИКА</b>\n\n📝 Всего: {stats['total']}\n✅ Опубликовано: {stats['published']}"
        bot.send_message(message.chat.id, text, parse_mode='HTML')

    @bot.message_handler(func=lambda m: m.text == "💾 Бэкап базы" and m.from_user.id in config.ADMIN_IDS)
    def backup_db(message):
        if os.path.exists('bot_data.db'):
            with open('bot_data.db', 'rb') as f:
                bot.send_document(message.chat.id, f)

    @bot.message_handler(func=lambda m: m.text == "💡 Запросы подписчиков" and m.from_user.id in config.ADMIN_IDS)
    def sub_requests(message):
        report = analyzer.analyze_comments()
        bot.send_message(message.chat.id, report, parse_mode="HTML")
