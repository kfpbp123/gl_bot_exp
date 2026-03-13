# utils/localizer.py

TRANSLATIONS = {
    "ru": {
        "welcome": "Добро пожаловать в Minecraft Bot! 🚀\nЯ помогу тебе создавать крутые посты для каналов.",
        "choose_lang": "Выберите язык:",
        "main_menu": "Главное меню:",
        "btn_create": "📝 Создать пост",
        "btn_stats": "📊 Статистика",
        "btn_settings": "⚙️ Настройки",
        "btn_persona": "🎭 Выбор стиля",
        "btn_channel": "📢 Выбор канала",
        "btn_add_channel": "➕ Добавить канал",
        "btn_queue_status": "📊 Статус очереди",
        "btn_export": "📊 Экспорт (CSV)",
        "btn_ad": "💰 Реклама",
        "btn_backup": "💾 Бэкап базы",
        "btn_requests": "💡 Запросы подписчиков",
        "ask_topic": "🤖 Отправь мне фото, текст или ссылку с описанием мода! 🚀",
        "generating": "⌛ ИИ генерирует текст про Minecraft мод, пожалуйста, подождите...",
        "error_ai": "❌ Ошибка при генерации текста. Попробуйте еще раз.",
        "success_gen": "{text}",
        "btn_add_photo": "🖼 Добавить фото",
        "btn_save": "✅ Сохранить",
        "btn_smart_queue": "🧠 Умная очередь (+{hours} ч)",
        "btn_now": "🚀 Сейчас",
        "btn_later": "📅 Позже",
        "btn_edit": "✏️ Правка",
        "btn_rewrite": "✨ Переписать",
        "btn_add_ad": "💰 +Реклама",
        "btn_cancel": "❌ Отмена",
        "btn_delete": "❌ Удалить",
        "processing_photo": "🎨 Обрабатываю фото...",
        "processing_album": "📸 Загружаю альбом...",
        "processing_album_ai": "🎨 Обрабатываю альбом...",
        "time_night": "🌙 Доброй ночи",
        "time_morning": "🌅 Доброе утро",
        "time_day": "☀️ Добрый день",
        "time_evening": "🌆 Добрый вечер",
        "stats_text": """📊 <b>СТАТИСТИКА БОТА</b> 📊

📝 Всего постов создано: <b>{total}</b>
✅ Успешно опубликовано: <b>{published}</b>
⏳ Ждут в очереди: <b>{queue}</b>
📅 Опубликовано сегодня: <b>{today}</b>
📢 Подключенных каналов: <b>{active_ch_count}</b>""",
        "queue_empty": "📭 Очередь пуста.",
        "queue_post_format": """╔═══📋 ПОСТ {index}/{total} ═══╗
{type_icon} <b>Тип:</b> {type_name}
📢 <b>Канал:</b> {channel}
⏰ <b>Время:</b> {time_str}

📝 <b>Превью:</b>
<i>{preview}</i>
╚════════════════════╝""",
        "ad_current": "Текущая реклама:\n{text}\n\nПришли новый текст рекламы:",
        "add_channel_prompt": "Отправь @username нового канала:",
        "choose_persona": "Выбери личность бота:",
        "choose_channel": "Выбери канал для публикации:",
        "comments_report_wait": "⏳ Читаю комментарии и анализирую...",
        "btn_clear_comments": "🗑 Очистить обработанные",
        "csv_wait": "⏳ Выгружаю данные в таблицу Excel...",
        "csv_empty": "📭 База данных пуста, выгружать нечего.",
        "backup_wait": "Выгружаю bot_data.db..."
    },
    "uz": {
        "welcome": "Minecraft Bot-ga xush kelibsiz! 🚀\nMen sizga kanallar uchun ajoyib postlar yaratishda yordam beraman.",
        "choose_lang": "Tilni tanlang:",
        "main_menu": "Asosiy menyu:",
        "btn_create": "📝 Post yaratish",
        "btn_stats": "📊 Statistika",
        "btn_settings": "⚙️ Sozlamalar",
        "btn_persona": "🎭 Uslubni tanlash",
        "btn_channel": "📢 Kanalni tanlash",
        "btn_add_channel": "➕ Kanal qo'shish",
        "btn_queue_status": "📊 Navbat holati",
        "btn_export": "📊 Eksport (CSV)",
        "btn_ad": "💰 Reklama",
        "btn_backup": "💾 Ma'lumotlar bazasi zaxirasi",
        "btn_requests": "💡 Obunachilar so'rovlari",
        "ask_topic": "🤖 Menga mod tavsifi bilan rasm, matn yoki havola yuboring! 🚀",
        "generating": "⌛ AI Minecraft modi haqida matn yaratmoqda, iltimos kuting...",
        "error_ai": "❌ Matn yaratishda xato. Qayta urinib ko'ring.",
        "success_gen": "{text}",
        "btn_add_photo": "🖼 Rasm qo'shish",
        "btn_save": "✅ Saqlash",
        "btn_smart_queue": "🧠 Aqlli navbat (+{hours} soat)",
        "btn_now": "🚀 Hozir",
        "btn_later": "📅 Keyinroq",
        "btn_edit": "✏️ Tahrirlash",
        "btn_rewrite": "✨ Qayta yozish",
        "btn_add_ad": "💰 +Reklama",
        "btn_cancel": "❌ Bekor qilish",
        "btn_delete": "❌ O'chirish",
        "processing_photo": "🎨 Rasmni qayta ishlayapman...",
        "processing_album": "📸 Albom yuklanmoqda...",
        "processing_album_ai": "🎨 Albom qayta ishlanmoqda...",
        "time_night": "🌙 Xayrli tun",
        "time_morning": "🌅 Xayrli tong",
        "time_day": "☀️ Xayrli kun",
        "time_evening": "🌆 Xayrli kech",
        "stats_text": """📊 <b>BOT STATISTIKASI</b> 📊

📝 Jami yaratilgan postlar: <b>{total}</b>
✅ Muvaffaqiyatli nashr etilgan: <b>{published}</b>
⏳ Navbatda kutayotganlar: <b>{queue}</b>
📅 Bugun nashr etilgan: <b>{today}</b>
📢 Ulangan kanallar: <b>{active_ch_count}</b>""",
        "queue_empty": "📭 Navbat bo'sh.",
        "queue_post_format": """╔═══📋 POST {index}/{total} ═══╗
{type_icon} <b>Turi:</b> {type_name}
📢 <b>Kanal:</b> {channel}
⏰ <b>Vaqt:</b> {time_str}

📝 <b>Ko'rib chiqish:</b>
<i>{preview}</i>
╚════════════════════╝""",
        "ad_current": "Joriy reklama:\n{text}\n\nYangi reklama matnini yuboring:",
        "add_channel_prompt": "Yangi kanalning @username yuboring:",
        "choose_persona": "Bot shaxsini tanlang:",
        "choose_channel": "Nashr qilish uchun kanalni tanlang:",
        "comments_report_wait": "⏳ Izohlarni o'qish va tahlil qilish...",
        "btn_clear_comments": "🗑 Tozalash",
        "csv_wait": "⏳ Ma'lumotlarni Excel jadvaliga eksport qilmoqdaman...",
        "csv_empty": "📭 Ma'lumotlar bazasi bo'sh, eksport qilinadigan narsa yo'q.",
        "backup_wait": "bot_data.db yuklanmoqda..."
    }
}

def t(key, lang="ru", **kwargs):
    text = TRANSLATIONS.get(lang, TRANSLATIONS["ru"]).get(key, key)
    return text.format(**kwargs)
