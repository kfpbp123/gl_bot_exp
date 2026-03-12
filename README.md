# 🚀 Minecraft Poster SaaS Platform

Профессиональная асинхронная платформа для автопостинга в Telegram с использованием ИИ (Gemini Pro) и автоматическим наложением вотермарков.

## 🏗 Новая архитектура (Clean Architecture)
Проект полностью переведен с синхронного `pyTelegramBotAPI` на современный асинхронный стек:
- **Bot Engine:** `aiogram 3.x` (Async)
- **Database:** `PostgreSQL` + `SQLAlchemy 2.0` (Async)
- **State Management:** `Redis` (для FSM состояний)
- **AI Service:** `Google Gemini Pro` (Async)
- **Image Processing:** `Pillow` (Async via `asyncio.to_thread`)
- **Logging:** `structlog` (структурированные логи)

## 📁 Структура проекта
- `bot/`: Хэндлеры, клавиатуры, состояния и мидлвари.
- `database/`: Модели таблиц, сессии и репозитории (CRUD).
- `services/`: Бизнес-логика (AI генерация постов).
- `utils/`: Вспомогательные модули (наложение вотермарков).
- `core/`: Глобальные настройки (`pydantic-settings`) и логирование.

## 🚀 Инструкция по запуску

### 1. Подготовка баз данных
Убедитесь, что у вас установлены:
- **PostgreSQL 16** (Создайте в pgAdmin пустую базу `mine_bot`)
- **Redis** (или Memurai для Windows)

### 2. Настройка окружения
Файл `.env` уже автоматически создан и содержит ваши токены. Если вы установили пароль в PostgreSQL отличный от `password`, измените его в строке:
```env
DATABASE_URL=postgresql+asyncpg://postgres:ВАШ_ПАРОЛЬ@localhost:5432/mine_bot
```

### 3. Инициализация таблиц
Запустите скрипт для создания структуры таблиц в PostgreSQL:
```bash
python init_db.py
```

### 4. Запуск бота
```bash
python main.py
```

## 🛠 Основные команды
- `/start` — Регистрация и приветствие.
- `/create` — Пошаговое создание поста: тема -> ИИ текст -> фото -> вотермарк -> черновик.

---
*Проект переработан и готов к масштабированию (SaaS Ready).*
