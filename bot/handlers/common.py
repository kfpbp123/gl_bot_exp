# bot/handlers/common.py
from aiogram import Router, types, F
from aiogram.filters import Command
from database.repositories import UserRepository
from bot.keyboards.main_menu import get_main_menu, get_lang_keyboard
from utils.localizer import t

router = Router()

@router.message(Command("start"))
async def cmd_start(message: types.Message, user_repo: UserRepository):
    user = await user_repo.get_user(message.from_user.id)
    
    if not user:
        await user_repo.upsert_user(
            user_id=message.from_user.id,
            username=message.from_user.username,
            language="ru" # По умолчанию
        )
        await message.answer(
            "🌍 Выберите язык / Tilni tanlang:", 
            reply_markup=get_lang_keyboard()
        )
    else:
        lang = user.language or "ru"
        await message.answer(
            t("welcome", lang),
            reply_markup=get_main_menu(lang)
        )

@router.message(Command("lang"))
async def cmd_lang(message: types.Message):
    await message.answer(
        "🌍 Выберите язык / Tilni tanlang:", 
        reply_markup=get_lang_keyboard()
    )

@router.callback_query(F.data.startswith("set_lang_"))
async def process_set_lang(callback: types.CallbackQuery, user_repo: UserRepository):
    lang = callback.data.split("_")[2]
    await user_repo.upsert_user(
        user_id=callback.from_user.id,
        username=callback.from_user.username,
        language=lang
    )
    
    await callback.message.edit_text("✅")
    await callback.message.answer(
        t("welcome", lang),
        reply_markup=get_main_menu(lang)
    )
    await callback.answer()
