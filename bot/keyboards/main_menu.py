# bot/keyboards/main_menu.py
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from utils.localizer import t

def get_lang_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🇷🇺 Русский", callback_data="set_lang_ru")],
        [InlineKeyboardButton(text="🇺🇿 O'zbekcha", callback_data="set_lang_uz")]
    ])

def get_main_menu(lang="ru"):
    kb = [
        [KeyboardButton(text=t("btn_create", lang))],
        [KeyboardButton(text=t("btn_stats", lang)), KeyboardButton(text=t("btn_settings", lang))]
    ]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)
