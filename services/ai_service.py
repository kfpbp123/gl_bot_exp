# services/ai_service.py
import google.generativeai as genai
from core.config import settings
from core.logging import logger
import re
import asyncio
import aiohttp
from bs4 import BeautifulSoup

class AIService:
    def __init__(self):
        genai.configure(api_key=settings.GEMINI_API_KEY.get_secret_value())
        # Используем flash 1.5 или 2.0 если доступна
        self.model = genai.GenerativeModel('gemini-1.5-flash')
        self._logger = logger.bind(service="AIService")
        
        self.personas = {
            "uz": """Ты — креативный редактор Telegram-канала о модах для Minecraft.
Я передам тебе текст. Вычлени главное и напиши пост. Уложись в 800 символов.
Пиши ТОЛЬКО на узбекском латинице. Если не смог найти версию напиши "1.21+".
Используй тег <blockquote expandable> для основного блока. Перепиши текст в более веселом, драйвовом и геймерском стиле. Добавь чуть больше эмодзи.

Формат:
📦 <b>[Название]</b>

<blockquote expandable><b>Bu nima?</b>
[Описание]

<b>Asosiy xususiyatlar:</b>
• [Фишка 1]
• [Фишка 2]

🎮 Versiya: [Версия]</blockquote>

<blockquote>💖 - zo`r
💔 - Unchamas</blockquote>

#Minecraft #[Категория]

ПРАВИЛА ДЛЯ ХЭШТЕГОВ (КРИТИЧЕСКИ ВАЖНО):
1. Внимательно проанализируй, о чем пост. Выбери строго ОДНУ категорию и напиши её хэштег: #Mods, #Maps, #Textures или #Shaders.
2. В конце поста должно быть ровно ДВА хэштега: #Minecraft и хэштег выбранной категории.
3. КАТЕГОРИЧЕСКИ ЗАПРЕЩЕНО писать название мода в виде хэштега! Не придумывай свои слова для хэштегов!
""",
            "ru": """Ты — креативный редактор Telegram-канала о модах для Minecraft.
Я передам тебе текст. Вычлени главное и напиши пост в драйвовом и веселом стиле. Уложись в 800 символов.
Пиши ТОЛЬКО на русском языке.
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

ПРАВИЛА ДЛЯ ХЭШТЕГОВ (КРИТИЧЕСКИ ВАЖНО):
1. Внимательно проанализируй, о чем пост. Выбери строго ОДНУ категорию и напиши её хэштег на русском: #Моды, #Карты, #Текстуры или #Шейдеры.
2. В конце поста должно быть ровно ДВА хэштега: #Minecraft и хэштег выбранной категории.
3. КАТЕГОРИЧЕСКИ ЗАПРЕЩЕНО писать название мода в виде хэштега! Не придумывай свои слова для хэштегов!
""",
            "en": """You are a creative editor for a Minecraft mods Telegram channel.
Extract the main points and write an engaging post. Keep it under 800 characters.
Write ONLY in English in an exciting tone.
Use the <blockquote expandable> tag for the main body.

Format:
📦 <b>[Mod Name]</b>

<blockquote expandable><b>What is it?</b>
[Description]

<b>Key Features:</b>
• [Feature 1]
• [Feature 2]

🎮 Version: [Version]</blockquote>

<blockquote>💖 - Awesome
💔 - Not great</blockquote>

#Minecraft #[Category]

HASHTAG RULES (CRITICAL):
1. Analyze the content and choose exactly ONE category hashtag from this list: #Mods, #Maps, #Textures, or #Shaders.
2. The post must end with exactly two hashtags: #Minecraft and the chosen category hashtag.
3. NEVER use the mod's name as a hashtag! Do not invent your own hashtags!
"""
        }

    def _extract_url(self, text: str) -> str | None:
        urls = re.findall(r'(https?://[^\s]+)', text)
        return urls[0] if urls else None

    async def _fetch_page_content(self, url: str) -> str:
        try:
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
            async with aiohttp.ClientSession(headers=headers) as session:
                async with session.get(url, timeout=10) as response:
                    if response.status == 200:
                        content = await response.text()
                        soup = BeautifulSoup(content, 'html.parser')
                        text = soup.get_text(separator=' ', strip=True)
                        return text[:5000]
            return ""
        except Exception as e:
            self._logger.warning("url_fetch_failed", url=url, error=str(e))
            return ""

    async def generate_post(self, topic: str, persona: str = "uz") -> str | None:
        try:
            self._logger.info("generating_post", topic=topic, persona=persona)
            
            url = self._extract_url(topic)
            site_context = ""
            if url:
                site_context = await self._fetch_page_content(url)
                if site_context:
                    site_context = f"\n\nКонтент с сайта:\n{site_context}"

            system_prompt = self.personas.get(persona, self.personas["uz"])
            full_prompt = f"{system_prompt}\n\nТема от пользователя: {topic}{site_context}\n\nЗАДАНИЕ: Напиши полноценный пост."
            
            loop = asyncio.get_event_loop()
            
            def sync_generate():
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
                    return response.candidates[0].content.parts[0].text if response.candidates[0].content.parts else None

            generated_text = await loop.run_in_executor(None, sync_generate)
            
            if generated_text:
                text = generated_text.strip()
                text = text.replace("```html", "").replace("```", "")
                text = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', text)
                return text
            
            return None

        except Exception as e:
            self._logger.error("ai_generation_failed", error=str(e))
            return None

    async def rewrite_post(self, text: str, style: str = "short") -> str:
        styles = {
            "short": "Сделай текст короче и лаконичнее. Оставь только самую суть, убери лишнюю воду.",
            "fun": "Перепиши текст в более веселом, драйвовом и геймерском стиле. Добавь чуть больше эмодзи.",
            "pro": "Сделай текст более профессиональным, строгим и информативным."
        }
        prompt_instruction = styles.get(style, "Улучши этот текст.")
        prompt = f"{prompt_instruction}\n\nВАЖНО: Сохрани HTML-теги форматирования (<b>, <blockquote>) и все хэштеги в конце.\n\nОригинальный текст:\n{text}"
        
        try:
            loop = asyncio.get_event_loop()
            def sync_rewrite():
                response = self.model.generate_content(prompt)
                return response.text
            
            rewritten_text = await loop.run_in_executor(None, sync_rewrite)
            if rewritten_text:
                final_text = rewritten_text.strip()
                final_text = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', final_text)
                return final_text
            return text
        except Exception as e:
            self._logger.error("ai_rewrite_failed", error=str(e))
            return text

ai_service = AIService()
