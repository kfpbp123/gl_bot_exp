# services/ai_service.py
import google.generativeai as genai
from core.config import settings
from core.logging import logger
import re
import asyncio

class AIService:
    def __init__(self):
        # Используем genai для настройки
        genai.configure(api_key=settings.GEMINI_API_KEY.get_secret_value())
        # Используем проверенную модель
        self.model = genai.GenerativeModel('gemini-1.5-flash')
        self._logger = logger.bind(service="AIService")
        
        self.system_prompt = """Ты — креативный редактор Telegram-канала о модах для Minecraft.
Вычлени главное и напиши пост. Уложись в 800 символов.
Используй тег <blockquote expandable> для основного блока.

Формат:
📦 <b>[Название]</b>

<blockquote expandable><b>Что это такое?</b>
[Описание]

<b>Главные фишки:</b>
• [Фишка 1]
• [Фишка 2]

🎮 Версия: [Версия]</blockquote>

<blockquote>💖 - Имба
💔 - Не оч</blockquote>

#Minecraft #[Категория]

ПРАВИЛА:
1. Выбери строго ОДНУ категорию: #Моды, #Карты, #Текстуры или #Шейдеры.
2. В конце ровно ДВА хэштега: #Minecraft и категория.
"""

    async def generate_post(self, topic: str) -> str | None:
        try:
            self._logger.info("generating_post", topic=topic)
            
            # Если запрос слишком короткий, просим ИИ придумать что-то креативное про майнкрафт
            full_prompt = f"{self.system_prompt}\n\nТема: {topic}\n\nВАЖНО: Если тема слишком короткая или непонятная, придумай описание для случайного популярного мода для Minecraft и оформи его."
            
            loop = asyncio.get_event_loop()
            def sync_generate():
                response = self.model.generate_content(full_prompt)
                try:
                    return response.text if response and response.text else None
                except Exception as e:
                    self._logger.error("ai_safety_block_or_error", error=str(e))
                    return None

            generated_text = await loop.run_in_executor(None, sync_generate)
            
            if generated_text:
                # Очистка от markdown-мусора
                text = generated_text.strip()
                text = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', text)
                return text
            
            return None

        except Exception as e:
            self._logger.error("ai_generation_failed", error=str(e))
            return None

ai_service = AIService()
