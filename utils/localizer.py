# utils/localizer.py

TRANSLATIONS = {
    "ru": {
        "welcome": "Добро пожаловать в Minecraft SaaS! 🚀\nЯ помогу тебе создавать крутые посты для каналов.",
        "choose_lang": "Выберите язык:",
        "main_menu": "Главное меню:",
        "btn_create": "📝 Создать пост",
        "btn_stats": "📊 Статистика",
        "btn_settings": "⚙️ Настройки",
        "ask_topic": "🤖 О чем должен быть пост? Напиши тему или краткое описание.",
        "generating": "⌛ ИИ генерирует текст про Minecraft мод, пожалуйста, подождите...",
        "error_ai": "❌ Ошибка при генерации текста. Попробуйте еще раз.",
        "success_gen": "📝 Сгенерированный текст:\n\n{text}",
        "btn_add_photo": "🖼 Добавить фото",
        "btn_save": "✅ Сохранить"
    },
    "uz": {
        "welcome": "Minecraft SaaS-ga xush kelibsiz! 🚀\nMen sizga kanallar uchun ajoyib postlar yaratishda yordam beraman.",
        "choose_lang": "Tilni tanlang:",
        "main_menu": "Asosiy menyu:",
        "btn_create": "📝 Post yaratish",
        "btn_stats": "📊 Statistika",
        "btn_settings": "⚙️ Sozlamalar",
        "ask_topic": "🤖 Post nima haqida bo'lishi kerak? Mavzu yoki qisqacha tavsif yozing.",
        "generating": "⌛ AI Minecraft modi haqida matn yaratmoqda, iltimos kuting...",
        "error_ai": "❌ Matn yaratishda xato. Qayta urinib ko'ring.",
        "success_gen": "📝 Yaratilgan matn:\n\n{text}",
        "btn_add_photo": "🖼 Rasm qo'shish",
        "btn_save": "✅ Saqlash"
    }
}

def t(key, lang="ru", **kwargs):
    text = TRANSLATIONS.get(lang, TRANSLATIONS["ru"]).get(key, key)
    return text.format(**kwargs)
