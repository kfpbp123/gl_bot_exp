# bot/handlers/posts.py
import os
import asyncio
from datetime import datetime, timedelta
from typing import List, Dict

from aiogram import Router, types, F, Bot
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import InputMediaPhoto, FSInputFile

from bot.states.post import PostDraftStates
from bot.keyboards.main_menu import get_draft_markup, get_main_menu, get_cancel_markup
from services.ai_service import ai_service
from utils.watermarker import watermarker
from database.repositories import PostRepository, UserRepository, ChannelRepository
from core.logging import logger
from core.config import settings
from utils.localizer import t

router = Router()

# Кэш для альбомов
album_cache: Dict[str, List[types.Message]] = {}

async def get_user_lang(user_id: int, user_repo: UserRepository) -> str:
    user = await user_repo.get_user(user_id)
    return user.language if user else "ru"

@router.message(F.text.in_({"📝 Создать пост", "📝 Post yaratish"}))
async def cmd_create_post(message: types.Message, state: FSMContext, user_repo: UserRepository):
    lang = await get_user_lang(message.from_user.id, user_repo)
    await state.set_state(PostDraftStates.waiting_for_topic)
    await message.answer(t("ask_topic", lang), reply_markup=get_cancel_markup(lang))

@router.message(PostDraftStates.waiting_for_topic, F.text == F.text) # Just a placeholder for text
async def process_text_input(message: types.Message, state: FSMContext, user_repo: UserRepository, bot: Bot):
    if message.text in {t("btn_cancel", "ru"), t("btn_cancel", "uz")}:
        lang = await get_user_lang(message.from_user.id, user_repo)
        await state.clear()
        await message.answer(t("main_menu", lang), reply_markup=get_main_menu(lang))
        return

    await handle_input(message, state, user_repo, bot)

@router.message(PostDraftStates.waiting_for_topic, F.photo)
async def process_photo_input(message: types.Message, state: FSMContext, user_repo: UserRepository, bot: Bot):
    if message.media_group_id:
        if message.media_group_id not in album_cache:
            album_cache[message.media_group_id] = []
            lang = await get_user_lang(message.from_user.id, user_repo)
            await message.answer(t("processing_album", lang))
            
            # Ждем 2 секунды, чтобы собрать все части альбома
            asyncio.create_task(process_media_group(message.media_group_id, message.chat.id, message.from_user.id, state, user_repo, bot))
        
        album_cache[message.media_group_id].append(message)
        return

    await handle_input(message, state, user_repo, bot)

async def handle_input(message: types.Message, state: FSMContext, user_repo: UserRepository, bot: Bot):
    lang = await get_user_lang(message.from_user.id, user_repo)
    user_input = message.caption if message.photo else message.text
    
    if not user_input and message.photo:
        user_input = "Опиши этот мод."
    elif not user_input:
        return

    sent_msg = await message.answer(t("generating", lang))
    generated_text = await ai_service.generate_post(user_input, lang)

    if not generated_text:
        await sent_msg.edit_text(t("error_ai", lang))
        return

    photo_id = None
    if message.photo:
        await sent_msg.edit_text(t("processing_photo", lang))
        photo = message.photo[-1]
        os.makedirs("temp", exist_ok=True)
        raw_path = f"temp/raw_{photo.file_id}.jpg"
        final_path = f"temp/wm_{photo.file_id}.jpg"
        
        await bot.download(photo, destination=raw_path)
        success = await watermarker.apply_watermark(raw_path, final_path)
        
        if success:
            preview_msg = await message.answer_photo(FSInputFile(final_path), caption=generated_text, parse_mode="HTML", reply_markup=get_draft_markup(lang))
            photo_id = preview_msg.photo[-1].file_id
        else:
            await message.answer(generated_text, parse_mode="HTML", reply_markup=get_draft_markup(lang))
        
        if os.path.exists(raw_path): os.remove(raw_path)
        if os.path.exists(final_path): os.remove(final_path)
    else:
        await message.answer(generated_text, parse_mode="HTML", reply_markup=get_draft_markup(lang))

    await state.update_data(draft_text=generated_text, draft_photo=photo_id)
    await sent_msg.delete()

async def process_media_group(mg_id: str, chat_id: int, user_id: int, state: FSMContext, user_repo: UserRepository, bot: Bot):
    await asyncio.sleep(2.5) # Даем время на загрузку всех фото
    messages = album_cache.pop(mg_id, None)
    if not messages: return
    
    messages.sort(key=lambda x: x.message_id)
    caption = next((m.caption for m in messages if m.caption), "Опиши мод")
    lang = await get_user_lang(user_id, user_repo)
    
    sent_msg = await bot.send_message(chat_id, t("processing_album_ai", lang))
    generated_text = await ai_service.generate_post(caption, lang)
    
    if not generated_text:
        await sent_msg.edit_text(t("error_ai", lang))
        return

    temp_files = []
    media = []
    
    os.makedirs("temp", exist_ok=True)
    
    for i, m in enumerate(messages):
        if not m.photo: continue
        photo = m.photo[-1]
        tin, tout = f"temp/in_{mg_id}_{i}.jpg", f"temp/out_{mg_id}_{i}.jpg"
        await bot.download(photo, destination=tin)
        await watermarker.apply_watermark(tin, tout)
        temp_files.append((tin, tout))
        media.append(InputMediaPhoto(media=FSInputFile(tout)))

    if media:
        media[0].caption = generated_text
        media[0].parse_mode = "HTML"
        sent_group = await bot.send_media_group(chat_id, media)
        photo_ids = [m.photo[-1].file_id for m in sent_group if m.photo]
        photo_id_str = ",".join(photo_ids)
        
        # Показываем меню управления под отдельным сообщением или текстом
        await bot.send_message(chat_id, "⬆️ " + t("success_gen", lang, text=""), reply_markup=get_draft_markup(lang))
        await state.update_data(draft_text=generated_text, draft_photo=photo_id_str)
    
    await sent_msg.delete()
    for tin, tout in temp_files:
        if os.path.exists(tin): os.remove(tin)
        if os.path.exists(tout): os.remove(tout)

# Обработка действий в меню черновика
@router.callback_query(F.data == "pub_now")
async def process_pub_now(callback: types.CallbackQuery, state: FSMContext, post_repo: PostRepository, bot: Bot):
    data = await state.get_data()
    text = data.get("draft_text")
    photo = data.get("draft_photo")
    lang = await get_user_lang(callback.from_user.id, post_repo) # UserRepository is also BaseRepository
    
    # В реальном боте мы бы отправляли в канал. Здесь пока просто помечаем и имитируем.
    # Но по заданию "перенести функционал", значит надо реализовать отправку.
    
    channel = settings.CHANNELS[0] # По умолчанию берем первый
    try:
        if photo:
            if "," in photo: # Альбом
                media = [InputMediaPhoto(media=p_id) for p_id in photo.split(",")]
                media[0].caption = text
                media[0].parse_mode = "HTML"
                await bot.send_media_group(channel, media)
            else:
                await bot.send_photo(channel, photo, caption=text, parse_mode="HTML")
        else:
            await bot.send_message(channel, text, parse_mode="HTML")
            
        await post_repo.create_post(callback.from_user.id, text, media_url=photo, channel_id=None) # TODO: channel_id
        await callback.message.answer("✅ Опубликовано в " + channel)
        await callback.message.delete()
    except Exception as e:
        await callback.answer(f"Ошибка: {e}", show_alert=True)

@router.callback_query(F.data == "add_to_smart_q")
async def process_smart_queue(callback: types.CallbackQuery, state: FSMContext, post_repo: PostRepository):
    data = await state.get_data()
    text = data.get("draft_text")
    photo = data.get("draft_photo")
    lang = await get_user_lang(callback.from_user.id, post_repo)
    
    last_time = await post_repo.get_last_scheduled_time()
    if not last_time or last_time < datetime.utcnow():
        scheduled_at = datetime.utcnow() + timedelta(hours=settings.SMART_QUEUE_INTERVAL_HOURS)
    else:
        scheduled_at = last_time + timedelta(hours=settings.SMART_QUEUE_INTERVAL_HOURS)
        
    post = await post_repo.create_post(callback.from_user.id, text, media_url=photo)
    await post_repo.update_post(post.id, scheduled_at=scheduled_at, status="scheduled")
    
    await callback.message.answer(f"⏳ Запланировано на {scheduled_at.strftime('%d.%m %H:%M')}")
    await callback.message.delete()
    await callback.answer()

@router.callback_query(F.data == "cancel_action")
async def process_cancel_draft(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.delete()
    await callback.answer("Удалено")

@router.callback_query(F.data == "rewrite_menu")
async def process_rewrite_menu(callback: types.CallbackQuery, lang: str = "ru"):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="⚡️ Короче", callback_data="rewrite_short")],
        [types.InlineKeyboardButton(text="🎉 Веселее", callback_data="rewrite_fun")],
        [types.InlineKeyboardButton(text="👔 Профи", callback_data="rewrite_pro")],
        [types.InlineKeyboardButton(text="⬅️ Назад", callback_data="back_to_draft")]
    ])
    await callback.message.edit_reply_markup(reply_markup=kb)

@router.callback_query(F.data.startswith("rewrite_"))
async def handle_rewrite(callback: types.CallbackQuery, state: FSMContext, user_repo: UserRepository):
    style = callback.data.split("_")[1]
    if style == "menu": return # Handled above
    
    data = await state.get_data()
    text = data.get("draft_text")
    lang = await get_user_lang(callback.from_user.id, user_repo)
    
    sent_msg = await callback.message.answer("✨ ...")
    new_text = await ai_service.rewrite_post(text, style)
    
    await state.update_data(draft_text=new_text)
    
    if callback.message.caption:
        await callback.message.edit_caption(caption=new_text, parse_mode="HTML", reply_markup=get_draft_markup(lang))
    else:
        await callback.message.edit_text(text=new_text, parse_mode="HTML", reply_markup=get_draft_markup(lang))
    
    await sent_msg.delete()
    await callback.answer()
