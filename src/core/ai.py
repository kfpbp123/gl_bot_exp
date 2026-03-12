from google import genai
import config
import re
import requests
from bs4 import BeautifulSoup

client = genai.Client(api_key=config.GEMINI_KEY)
MODEL_ID = "gemini-2.5-flash"

PERSONAS = {
    "uz": {
        "gamer": "Geymer uslubi: drive, emojilar ko'p, 'imba', 'top' kabi so'zlar bilan.",
        "scientist": "Aqlli olim: Minecraft mexanikasini chuqur tushuntiradi, faktlar bilan.",
        "crazy": "Jinni professor: g'ayratli, biroz g'alati, hayqiriqlar bilan!",
        "minimalist": "Minimalist: faqat eng muhim narsa, qisqa va lo'nda.",
        "storyteller": "Hikoyachi: mod haqida kichik sarguzasht kabi yozadi.",
        "critic": "Qattiqqo'l tanqidchi: modning ham plyus, ham minuslarini topadi.",
        "cheerleader": "Pozitiv: juda quvnoq, hammani modni yuklab olishga chorlaydi.",
        "mystery": "Sirli: mod sirlari haqida qiziqtirib yozadi.",
        "helper": "Yordamchi: survival rejimida bu mod qanday yordam berishiga e'tibor qaratadi.",
        "architect": "Arxitektor: dekorativ modlar uchun ideal, go'zallik haqida.",
        "classic": "Klassik: oddiy va tushunarli reklama uslubi.",
        "news": "Yangiliklar: jurnalistik uslub, rasmiy va aniq.",
        "friend": "Yaqin do'st: xuddi do'stiga maslahat bergandek samimiy.",
        "villager": "Qishloqi: biroz kulgili, Minecraft dunyosidan kelib chiqib.",
        "og": "OG Gamer: eski Minecraft versiyalarini eslab, nostalgiya bilan."
    }
    # Аналогично для RU и EN
}

PROMPTS = {
    "uz": """Sen Minecraft modlari uchun kreativ Telegram redaktorisang.
Senga matn beraman, sen esa uni [STYLE] uslubida yozib ber. 800 belgidan oshmasin.
Faqat O'zbek tilida (lotin) yoz.

Uslub: [STYLE_DESC]

Format:
📦 <b>[Nomi]</b>

<blockquote expandable><b>Bu nima?</b>
[Tavsif]

<b>Asosiy xususiyatlar:</b>
• [Fakt 1]
• [Fakt 2]

🎮 Versiya: [Versiya]</blockquote>

<blockquote>💖 - zo`r
💔 - Unchamas</blockquote>

#Minecraft #[Kategoriya]
""",
    # RU и EN промпты...
}

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

def extract_url(text):
    urls = re.findall(r'(https?://[^\s]+)', text)
    return urls[0] if urls else None

def fetch_page_content(url):
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.content, 'html.parser')
        text = soup.get_text(separator=' ', strip=True)
        return text[:5000] 
    except Exception as e:
        print(f"⚠️ Не смог прочитать сайт {url}: {e}")
        return ""

def generate_post(user_input, persona="uz"):
    url = extract_url(user_input)
    site_context = ""
    
    if url:
        page_text = fetch_page_content(url)
        site_context = f"\n\nИнформация с сайта:\n{page_text}"

    selected_prompt = PROMPTS.get(persona, PROMPTS["uz"])
    
    prompt = f"{selected_prompt}\n\nСырая информация от пользователя:\n{user_input}{site_context}"
    response = client.models.generate_content(model=MODEL_ID, contents=prompt)
    
    final_text = response.text.strip()
    # Конвертируем Markdown-звездочки в HTML-теги для жирного текста
    final_text = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', final_text)
    
    return final_text

def rewrite_post(text, style="short"):
    styles = {
        "short": "Сделай текст короче и лаконичнее. Оставь только самую суть, убери лишнюю воду.",
        "fun": "Перепиши текст в более веселом, драйвовом и геймерском стиле. Добавь чуть больше эмодзи.",
        "pro": "Сделай текст более профессиональным, строгим и информативным."
    }
    prompt_instruction = styles.get(style, "Улучши этот текст.")
    prompt = f"{prompt_instruction}\n\nВАЖНО: Сохрани HTML-теги форматирования (<b>, <blockquote>) и все хэштеги в конце.\n\nОригинальный текст:\n{text}"
    
    try:
        response = client.models.generate_content(model=MODEL_ID, contents=prompt)
        final_text = response.text.strip()
        final_text = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', final_text)
        return final_text
    except Exception as e:
        print(f"❌ Ошибка рерайта: {e}")
        return text