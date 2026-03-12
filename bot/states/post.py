# bot/states/post.py
from aiogram.fsm.state import State, StatesGroup

class PostDraftStates(StatesGroup):
    waiting_for_topic = State()      # Ввод темы для ИИ
    waiting_for_generation = State() # Процесс работы Gemini
    reviewing_draft = State()        # Редактирование текста
    waiting_for_media = State()      # Добавление картинки (с вотермарком)
