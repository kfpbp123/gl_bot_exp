# services/ai_service.py
import google.generativeai as genai
from google.generativeai.types import GenerateContentResponse
from core.config import settings
from core.logging import logger

class AIService:
    def __init__(self):
        # Инициализируем Gemini API через конфиг
        genai.configure(api_key=settings.GEMINI_API_KEY.get_secret_value())
        self.model = genai.GenerativeModel('gemini-pro')
        self._logger = logger.bind(service="AIService")

    async def generate_post(self, prompt: str, context: str | None = None) -> str | None:
        """
        Асинхронная генерация текста поста.
        """
        full_prompt = f"Контекст: {context}\n\nЗадание: {prompt}" if context else prompt
        
        try:
            self._logger.info("generating_post", prompt_len=len(full_prompt))
            
            # Официальный асинхронный метод Gemini
            response: GenerateContentResponse = await self.model.generate_content_async(
                full_prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.7,
                    top_p=0.9,
                    max_output_tokens=1024,
                )
            )
            
            if response.text:
                self._logger.info("post_generated_successfully")
                return response.text
            
            return None

        except Exception as e:
            self._logger.error("ai_generation_failed", error=str(e))
            return None

# Экспортируем синглтон
ai_service = AIService()
