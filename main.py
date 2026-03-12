import telebot
import time
import config
from src.core import database
from src.bot import scheduler
from src.bot.handlers import common, user, admin

# Инициализация БД
database.init_db()

# Инициализация Бота
bot = telebot.TeleBot(config.TELEGRAM_TOKEN)

# Регистрация обработчиков
common.register_handlers(bot)
user.register_user_handlers(bot)
admin.register_admin_handlers(bot)

# Запуск планировщика
scheduler.init_scheduler(bot)

if __name__ == "__main__":
    print("🤖 Бот Minecraft Poster (Restructured) запущен!")
    
    # Удаляем вебхук перед запуском polling, чтобы избежать ошибки 409 Conflict
    bot.remove_webhook()
    time.sleep(1)
    
    while True:
        try:
            # Используем меньший таймаут для polling и увеличиваем long_polling_timeout
            bot.polling(none_stop=True, timeout=20, long_polling_timeout=20)
        except Exception as e:
            if "Read timed out" in str(e):
                # Это нормальная ошибка при долгом ожидании, просто перезапускаем
                time.sleep(1)
                continue
            print(f"❌ Ошибка Polling: {e}")
            time.sleep(5)
