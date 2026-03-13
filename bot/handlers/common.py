# bot/handlers/common.py
from aiogram import Router, types
from aiogram.filters import Command
from database.repositories import UserRepository
from bot.keyboards.main_menu import get_main_menu

router = Router()

@router.message(Command("start"))
async def cmd_start(message: types.Message, user_repo: UserRepository):
    # Автоматически сохраняем/обновляем пользователя в БД
    await user_repo.upsert_user(
        user_id=message.from_user.id,
        username=message.from_user.username,
        language=message.from_user.language_code or "ru"
    )
    
    await message.answer(
        f"Привет, {message.from_user.full_name}! 🚀\n\n"
        "Я — твоя SaaS платформа для автопостинга про Minecraft моды.\n"
        "Нажми кнопку ниже или напиши /create, чтобы начать.",
        reply_markup=get_main_menu()
    )
