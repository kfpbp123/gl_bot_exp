# bot/handlers/posts.py
from aiogram import Router, types, F, Bot
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from bot.states.post import PostDraftStates
from services.ai_service import ai_service
from utils.watermarker import watermarker
from database.repositories import PostRepository
from core.logging import logger
import os

router = Router()

@router.message(Command("create"))
async def start_draft(message: types.Message, state: FSMContext):
    """Начало процесса создания поста"""
    await state.set_state(PostDraftStates.waiting_for_topic)
    await message.answer("🤖 О чем должен быть пост? Напиши тему или краткое описание.")

@router.message(PostDraftStates.waiting_for_topic)
async def process_topic(message: types.Message, state: FSMContext):
    """Отправка запроса в Gemini"""
    topic = message.text
    await state.update_data(topic=topic)
    
    # Информируем пользователя о начале работы ИИ
    sent_msg = await message.answer("⌛ ИИ генерирует текст, пожалуйста, подождите...")
    await state.set_state(PostDraftStates.waiting_for_generation)

    # Вызываем асинхронный ИИ-сервис
    prompt = f"Напиши интересный и вовлекающий пост для Telegram на тему: {topic}. Используй эмодзи и структурируй текст."
    generated_text = await ai_service.generate_post(prompt=prompt)

    if not generated_text:
        await sent_msg.edit_text("❌ Ошибка при генерации текста. Попробуйте еще раз.")
        await state.clear()
        return

    # Сохраняем результат в FSM
    await state.update_data(generated_text=generated_text)
    await state.set_state(PostDraftStates.reviewing_draft)
    
    kb = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="🖼 Добавить фото с вотермарком", callback_data="add_photo")],
        [types.InlineKeyboardButton(text="✅ Сохранить как черновик", callback_data="save_only_text")],
        [types.InlineKeyboardButton(text="🔄 Сгенерировать заново", callback_data="regenerate")]
    ])
    
    await sent_msg.edit_text(f"📝 Сгенерированный текст:\n\n{generated_text}", reply_markup=kb)

@router.callback_query(F.data == "add_photo", PostDraftStates.reviewing_draft)
async def ask_for_photo(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(PostDraftStates.waiting_for_media)
    await callback.message.answer("📸 Отправьте изображение, на которое нужно наложить вотермарк.")
    await callback.answer()

@router.message(PostDraftStates.waiting_for_media, F.photo)
async def process_photo(message: types.Message, state: FSMContext, bot: Bot):
    """Асинхронное наложение вотермарка"""
    photo = message.photo[-1]
    
    # Создаем папку temp если её нет
    os.makedirs("temp", exist_ok=True)
    
    raw_path = f"temp/raw_{photo.file_id}.jpg"
    final_path = f"temp/wm_{photo.file_id}.jpg"
    
    # Скачиваем фото
    await bot.download(photo, destination=raw_path)
    
    # Накладываем вотермарк в отдельном потоке (не блокирует бота)
    msg = await message.answer("🎨 Накладываю вотермарк...")
    success = await watermarker.apply_watermark(raw_path, final_path)
    
    if success:
        await state.update_data(media_path=final_path)
        await message.answer_photo(
            types.FSInputFile(final_path), 
            caption="✅ Вотермарк успешно наложен! Сохранить этот пост?"
        )
        
        kb = types.InlineKeyboardMarkup(inline_keyboard=[
            [types.InlineKeyboardButton(text="✅ Да, сохранить", callback_data="save_full_post")],
            [types.InlineKeyboardButton(text="❌ Отмена", callback_data="cancel")]
        ])
        await message.answer("Что делаем дальше?", reply_markup=kb)
    else:
        await message.answer("❌ Ошибка при обработке фото.")
    
    await msg.delete()

@router.callback_query(F.data == "save_full_post", PostDraftStates.waiting_for_media)
async def finalize_post(callback: types.CallbackQuery, state: FSMContext, post_repo: PostRepository):
    """Сохранение поста в PostgreSQL"""
    data = await state.get_data()
    
    post = await post_repo.create_post(
        user_id=callback.from_user.id,
        text=data.get("generated_text"),
        media_url=data.get("media_path")
    )
    
    await callback.message.answer(f"🚀 Пост сохранен в черновики! (ID: {post.id})")
    await state.clear()
    await callback.answer()
