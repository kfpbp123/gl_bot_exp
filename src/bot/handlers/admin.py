import telebot
from src.core import database
from src.bot import keyboards
from src.utils import analyzer
import config
import os
import time

def register_admin_handlers(bot: telebot.TeleBot):
    @bot.message_handler(func=lambda m: m.text in ["🛡️ Админ-панель", "🛡️ Admin paneli"] and m.from_user.id in config.ADMIN_IDS)
    def admin_panel(message):
        bot.send_message(message.chat.id, "🛡️ Панель администратора", reply_markup=keyboards.get_admin_menu())

    @bot.message_handler(func=lambda m: m.text == "👥 Список пользователей" and m.from_user.id in config.ADMIN_IDS)
    def list_users(message):
        users = database.get_all_users()
        text = f"👥 <b>Всего пользователей: {len(users)}</b>\n\n"
        for u in users[:20]: # Показываем первых 20
            text += f"👤 {u[1]} (ID: {u[0]}) | {u[5] or 'uz'}\n"
        bot.send_message(message.chat.id, text, parse_mode='HTML')

    @bot.message_handler(func=lambda m: m.text == "📈 Общая статистика" and m.from_user.id in config.ADMIN_IDS)
    def global_stats(message):
        stats = database.get_admin_stats()
        text = f"📊 <b>ОБЩАЯ СТАТИСТИКА</b>\n\n📝 Всего постов: {stats['total']}\n✅ Опубликовано: {stats['published']}\n⏳ В очереди: {stats['queue']}"
        bot.send_message(message.chat.id, text, parse_mode='HTML')

    @bot.message_handler(func=lambda m: m.text == "💰 Реклама" and m.from_user.id in config.ADMIN_IDS)
    def broadcast_cmd(message):
        msg = bot.send_message(message.chat.id, "📢 Введите текст для рассылки всем пользователям (или нажми '❌ Отмена'):", reply_markup=keyboards.get_cancel_markup())
        bot.register_next_step_handler(msg, process_broadcast, bot)

    @bot.message_handler(func=lambda m: m.text == "💾 Бэкап базы" and m.from_user.id in config.ADMIN_IDS)
    def backup_db(message):
        if os.path.exists('bot_data.db'):
            with open('bot_data.db', 'rb') as f:
                bot.send_document(message.chat.id, f)

    @bot.message_handler(func=lambda m: m.text == "💡 Запросы подписчиков" and m.from_user.id in config.ADMIN_IDS)
    def sub_requests(message):
        report = analyzer.analyze_comments()
        bot.send_message(message.chat.id, report, parse_mode="HTML")

def process_broadcast(message, bot):
    if message.text in ["❌ Отмена", "❌ Bekor qilish"]:
        bot.send_message(message.chat.id, "Рассылка отменена.", reply_markup=keyboards.get_admin_menu())
        return

    users = database.get_all_users()
    count = 0
    bot.send_message(message.chat.id, f"🚀 Начинаю рассылку на {len(users)} пользователей...")
    
    for user in users:
        try:
            bot.send_message(user[0], message.text)
            count += 1
            time.sleep(0.05) # Защита от спам-фильтра
        except:
            pass
            
    bot.send_message(message.chat.id, f"✅ Рассылка завершена! Получили: {count} чел.")
