# services/ai_service.py
import google.generativeai as genai
from core.config import settings
from core.logging import logger
import re
import asyncio

class AIService:
    def __init__(self):
        genai.configure(api_key=settings.GEMINI_API_KEY.get_secret_value())
        # Используем flash 1.5 - она самая стабильная для таких задач
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
            
            # Улучшенный промпт для коротких запросов
            full_prompt = f"{self.system_prompt}\n\nТема от пользователя: {topic}\n\nЗАДАНИЕ: Напиши полноценный пост про любой интересный Minecraft мод, даже если тема выше слишком короткая."
            
            loop = asyncio.get_event_loop()
            
            def sync_generate():
                # Настройка безопасности (отключаем блокировку на простые слова)
                safety_settings = [
                    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
                    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
                    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
                    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
                ]
                
                response = self.model.generate_content(
                    full_prompt,
                    safety_settings=safety_settings
                )
                
                if not response.candidates:
                    return None
                    
                try:
                    return response.text
                except Exception:
                    # Если текст заблокирован фильтрами, возвращаем текст из первой части (если есть)
                    return response.candidates[0].content.parts[0].text if response.candidates[0].content.parts else None

            generated_text = await loop.run_in_executor(None, sync_generate)
            
            if generated_text:
                text = generated_text.strip()
                # Убираем возможные артефакты Markdown
                text = text.replace("```html", "").replace("```", "")
                text = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', text)
                return text
            
            return None

        except Exception as e:
            self._logger.error("ai_generation_failed", error=str(e))
            return None

ai_service = AIService()
