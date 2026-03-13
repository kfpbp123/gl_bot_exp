# bot/states/post.py
from aiogram.fsm.state import State, StatesGroup

class PostDraftStates(StatesGroup):
    waiting_for_topic = State()
    waiting_for_generation = State()
    reviewing_draft = State()
    waiting_for_media = State()
    waiting_for_edit_text = State()
    waiting_for_custom_time = State()

class AdminStates(StatesGroup):
    waiting_for_ad_text = State()
    waiting_for_new_channel = State()
