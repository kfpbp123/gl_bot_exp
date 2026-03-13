# bot/handlers/common.py
import os
import csv
from datetime import datetime
from aiogram import Router, types, F, Bot
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from database.repositories import UserRepository, PostRepository, ChannelRepository, CommentRepository
from bot.keyboards.main_menu import get_main_menu, get_lang_keyboard, get_cancel_markup
from bot.states.post import AdminStates
from utils.localizer import t
from core.config import settings

router = Router()

async def get_user_lang(user_id: int, user_repo: UserRepository) -> str:
    user = await user_repo.get_user(user_id)
    return user.language if user else "ru"

@router.message(Command("start"))
async def cmd_start(message: types.Message, user_repo: UserRepository):
    user = await user_repo.get_user(message.from_user.id)
    
    if not user:
        await user_repo.upsert_user(
            user_id=message.from_user.id,
            username=message.from_user.username,
            language="ru"
        )
        await message.answer(
            "🌍 Выберите язык / Tilni tanlang / Choose language:", 
            reply_markup=get_lang_keyboard()
        )
    else:
        lang = user.language or "ru"
        await message.answer(
            t("welcome", lang),
            reply_markup=get_main_menu(lang)
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

@router.message(F.text.in_({"📊 Статистика", "📊 Statistika"}))
async def show_stats(message: types.Message, post_repo: PostRepository, user_repo: UserRepository):
    lang = await get_user_lang(message.from_user.id, user_repo)
    stats = await post_repo.get_stats()
    # TODO: active_ch_count
    active_ch_count = len(settings.CHANNELS)
    
    await message.answer(
        t("stats_text", lang, **stats, active_ch_count=active_ch_count),
        parse_mode="HTML"
    )

@router.message(F.text.in_({"📊 Экспорт (CSV)", "📊 Eksport (CSV)"}))
async def export_csv(message: types.Message, post_repo: PostRepository, user_repo: UserRepository, bot: Bot):
    lang = await get_user_lang(message.from_user.id, user_repo)
    await message.answer(t("csv_wait", lang))
    
    posts = await post_repo.get_all_pending() # Or all posts
    if not posts:
        await message.answer(t("csv_empty", lang))
        return
        
    filename = f"posts_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["ID", "Text", "Media", "Status", "Scheduled At"])
        for p in posts:
            writer.writerow([p.id, p.text, p.media_url, p.status, p.scheduled_at])
            
    await message.answer_document(types.FSInputFile(filename))
    os.remove(filename)

@router.message(F.text.in_({"💰 Реклама", "💰 Reklama"}))
async def manage_ad(message: types.Message, state: FSMContext, user_repo: UserRepository):
    lang = await get_user_lang(message.from_user.id, user_repo)
    # В этой версии мы храним текст рекламы в файле или БД.
    ad_text = "ПУСТО"
    if os.path.exists("ad.txt"):
        with open("ad.txt", "r", encoding="utf-8") as f: ad_text = f.read()
        
    await state.set_state(AdminStates.waiting_for_ad_text)
    await message.answer(t("ad_current", lang, text=ad_text), reply_markup=get_cancel_markup(lang))

@router.message(AdminStates.waiting_for_ad_text)
async def process_ad_text(message: types.Message, state: FSMContext, user_repo: UserRepository):
    lang = await get_user_lang(message.from_user.id, user_repo)
    if message.text in {t("btn_cancel", "ru"), t("btn_cancel", "uz")}:
        await state.clear()
        await message.answer(t("main_menu", lang), reply_markup=get_main_menu(lang))
        return
        
    with open("ad.txt", "w", encoding="utf-8") as f: f.write(message.text)
    await state.clear()
    await message.answer("✅ Реклама обновлена", reply_markup=get_main_menu(lang))

@router.message(F.text.in_({"💾 Бэкап базы", "💾 Ma'lumotlar bazasi zaxirasi"}))
async def backup_db(message: types.Message, user_repo: UserRepository):
    lang = await get_user_lang(message.from_user.id, user_repo)
    await message.answer(t("backup_wait", lang))
    # В PostgreSQL сложнее просто файл отправить, но мы можем отправить .env или другие файлы
    # Если используется SQLite (bot_data.db), то отправляем его.
    if os.path.exists("bot_data.db"):
        await message.answer_document(types.FSInputFile("bot_data.db"))
    else:
        await message.answer("Файл БД не найден (используется PostgreSQL)")

@router.message(F.text.in_({"🎭 Выбор стиля", "🎭 Uslubni tanlash"}))
async def choose_persona(message: types.Message, user_repo: UserRepository):
    lang = await get_user_lang(message.from_user.id, user_repo)
    await message.answer(t("choose_persona", lang), reply_markup=get_lang_keyboard())

@router.message(F.text.in_({"❌ Отмена", "❌ Bekor qilish"}))
async def cmd_cancel(message: types.Message, state: FSMContext, user_repo: UserRepository):
    lang = await get_user_lang(message.from_user.id, user_repo)
    await state.clear()
    await message.answer(t("main_menu", lang), reply_markup=get_main_menu(lang))

@router.message(F.text.in_({"📢 Выбор канала", "📢 Kanalni tanlash"}))
async def choose_channel(message: types.Message, user_repo: UserRepository):
    lang = await get_user_lang(message.from_user.id, user_repo)
    user = await user_repo.get_user(message.from_user.id)
    active = user.active_channel or settings.CHANNELS[0]
    
    kb = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text=f"{'✅ ' if ch == active else ''}{ch}", callback_data=f"set_channel_{ch}")] for ch in settings.CHANNELS
    ])
    await message.answer(t("choose_channel", lang), reply_markup=kb)

@router.callback_query(F.data.startswith("set_channel_"))
async def process_set_channel(callback: types.CallbackQuery, user_repo: UserRepository):
    channel = callback.data.split("_")[2]
    lang = await get_user_lang(callback.from_user.id, user_repo)
    
    await user_repo.upsert_user(
        user_id=callback.from_user.id,
        active_channel=channel
    )
    
    await callback.message.edit_text(f"✅ {channel}")
    await callback.answer()

@router.message(F.text.in_({"💡 Запросы подписчиков", "💡 Obunachilar so'rovlari"}))
async def subscriber_requests(message: types.Message, user_repo: UserRepository, comment_repo: CommentRepository):
    lang = await get_user_lang(message.from_user.id, user_repo)
    await message.answer(t("comments_report_wait", lang))
    
    comments = await comment_repo.get_all_comments()
    if not comments:
        await message.answer(t("queue_empty", lang)) # Reuse empty status
        return

    # Собираем все комментарии в один текст
    comments_text = "\n".join([f"- {c.user_name}: {c.text}" for c in comments])
    
    # Мы можем вызвать ai_service здесь для анализа
    prompt = f"""
    Ты — аналитик Telegram-канала о модах Minecraft. Составь выжимку:
    {comments_text}
    """
    
    try:
        from services.ai_service import ai_service
        # Используем простую генерацию для отчета
        report = await ai_service.generate_post(prompt, lang)
        
        kb = types.InlineKeyboardMarkup(inline_keyboard=[
            [types.InlineKeyboardButton(text=t("btn_clear_comments", lang), callback_data="clear_comments_db")]
        ])
        await message.answer(report, parse_mode="HTML", reply_markup=kb)
    except Exception as e:
        await message.answer(f"Ошибка анализа: {e}")

@router.callback_query(F.data == "clear_comments_db")
async def process_clear_comments(callback: types.CallbackQuery, comment_repo: CommentRepository):
    await comment_repo.clear_comments()
    await callback.message.edit_text("✅ Очищено / Tozalandi")
    await callback.answer()
