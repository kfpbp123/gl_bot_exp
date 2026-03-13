# bot/keyboards/main_menu.py
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from utils.localizer import t
from core.config import settings

def get_lang_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🇷🇺 Русский", callback_data="set_lang_ru")],
        [InlineKeyboardButton(text="🇺🇿 O'zbekcha", callback_data="set_lang_uz")],
        [InlineKeyboardButton(text="🇬🇧 English", callback_data="set_lang_en")]
    ])

def get_main_menu(lang="ru"):
    kb = [
        [KeyboardButton(text=t("btn_create", lang))],
        [KeyboardButton(text=t("btn_persona", lang)), KeyboardButton(text=t("btn_channel", lang))],
        [KeyboardButton(text=t("btn_add_channel", lang)), KeyboardButton(text=t("btn_queue_status", lang))],
        [KeyboardButton(text=t("btn_stats", lang)), KeyboardButton(text=t("btn_export", lang))],
        [KeyboardButton(text=t("btn_ad", lang)), KeyboardButton(text=t("btn_backup", lang))],
        [KeyboardButton(text=t("btn_requests", lang))]
    ]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

def get_cancel_markup(lang="ru"):
    kb = [[KeyboardButton(text=t("btn_cancel", lang))]]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

def get_draft_markup(lang="ru"):
    hours = settings.SMART_QUEUE_INTERVAL_HOURS
    kb = [
        [InlineKeyboardButton(text=t("btn_smart_queue", lang, hours=hours), callback_data="add_to_smart_q")],
        [
            InlineKeyboardButton(text=t("btn_now", lang), callback_data="pub_now"),
            InlineKeyboardButton(text=t("btn_later", lang), callback_data="pub_queue_menu")
        ],
        [
            InlineKeyboardButton(text=t("btn_edit", lang), callback_data="edit_text"),
            InlineKeyboardButton(text=t("btn_rewrite", lang), callback_data="rewrite_menu")
        ],
        [
            InlineKeyboardButton(text=t("btn_add_ad", lang), callback_data="add_ad"),
            InlineKeyboardButton(text=t("btn_delete", lang), callback_data="cancel_action")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=kb)
