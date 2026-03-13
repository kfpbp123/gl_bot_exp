# services/ai_service.py
import google.generativeai as genai
from core.config import settings
from core.logging import logger
import re

class AIService:
    def __init__(self):
        genai.configure(api_key=settings.GEMINI_API_KEY.get_secret_value())
        # Используем актуальную модель 1.5-flash
        self.model = genai.GenerativeModel('gemini-1.5-flash')
        self._logger = logger.bind(service="AIService")
        
        # Инструкции из вашего исходного плана
        self.system_prompt = """Ты — креативный редактор Telegram-канала о модах для Minecraft.
Я передам тебе текст или тему. Вычлени главное и напиши пост. Уложись в 800 символов.
Используй тег <blockquote expandable> для основного блока. Пиши в драйвовом и геймерском стиле.

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
3. ЗАПРЕЩЕНО писать название мода в виде хэштега!
"""

    async def generate_post(self, topic: str) -> str | None:
        try:
            self._logger.info("generating_post", topic=topic)
            
            prompt = f"{self.system_prompt}\n\nТема/Текст от пользователя: {topic}"
            
            # Асинхронная генерация
            response = await self.model.generate_content_async(prompt)
            
            if response.text:
                text = response.text.strip()
                # Конвертируем Markdown-звездочки в HTML (aiogram любит <b>)
                text = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', text)
                return text
            
            return None

        except Exception as e:
            self._logger.error("ai_generation_failed", error=str(e))
            return None

ai_service = AIService()
