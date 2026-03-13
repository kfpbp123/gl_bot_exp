# bot/handlers/posts.py
from aiogram import Router, types, F, Bot
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from bot.states.post import PostDraftStates
from services.ai_service import ai_service
from utils.watermarker import watermarker
from database.repositories import PostRepository, UserRepository
from core.logging import logger
from utils.localizer import t
import os

router = Router()

async def get_user_lang(user_id, user_repo):
    user = await user_repo.get_user(user_id)
    return user.language if user else "ru"

@router.message(Command("create"))
@router.message(F.text.in_({"📝 Создать пост", "📝 Post yaratish"}))
async def start_draft(message: types.Message, state: FSMContext, user_repo: UserRepository):
    lang = await get_user_lang(message.from_user.id, user_repo)
    await state.set_state(PostDraftStates.waiting_for_topic)
    await message.answer(t("ask_topic", lang))

@router.message(PostDraftStates.waiting_for_topic)
async def process_topic(message: types.Message, state: FSMContext, user_repo: UserRepository):
    lang = await get_user_lang(message.from_user.id, user_repo)
    topic = message.text
    await state.update_data(topic=topic, lang=lang)
    
    sent_msg = await message.answer(t("generating", lang))
    await state.set_state(PostDraftStates.waiting_for_generation)

    generated_text = await ai_service.generate_post(topic)

    if not generated_text:
        await sent_msg.edit_text(t("error_ai", lang))
        await state.clear()
        return

    await state.update_data(generated_text=generated_text)
    await state.set_state(PostDraftStates.reviewing_draft)
    
    kb = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text=t("btn_add_photo", lang), callback_data="add_photo")],
        [types.InlineKeyboardButton(text=t("btn_save", lang), callback_data="save_only_text")]
    ])
    
    await sent_msg.edit_text(t("success_gen", lang, text=generated_text), reply_markup=kb)

@router.callback_query(F.data == "add_photo", PostDraftStates.reviewing_draft)
async def ask_for_photo(callback: types.CallbackQuery, state: FSMContext, user_repo: UserRepository):
    lang = await get_user_lang(callback.from_user.id, user_repo)
    await state.set_state(PostDraftStates.waiting_for_media)
    await callback.message.answer("📸 Send photo / Rasm yuboring")
    await callback.answer()

@router.message(PostDraftStates.waiting_for_media, F.photo)
async def process_photo(message: types.Message, state: FSMContext, bot: Bot):
    photo = message.photo[-1]
    os.makedirs("temp", exist_ok=True)
    raw_path = f"temp/raw_{photo.file_id}.jpg"
    final_path = f"temp/wm_{photo.file_id}.jpg"
    
    await bot.download(photo, destination=raw_path)
    msg = await message.answer("🎨 ...")
    
    # Временно просто сохраняем без сложного вотермарка для теста
    success = await watermarker.apply_watermark(raw_path, final_path)
    
    if success:
        await state.update_data(media_path=final_path)
        await message.answer_photo(types.FSInputFile(final_path), caption="✅ OK?")
    else:
        await message.answer("❌ Error")
    await msg.delete()
