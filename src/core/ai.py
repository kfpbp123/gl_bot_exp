from google import genai
import config
import re
import requests
from bs4 import BeautifulSoup

client = genai.Client(api_key=config.GEMINI_KEY)
MODEL_ID = "gemini-2.0-flash"

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
    },
    "ru": {
        "gamer": "Геймерский стиль: драйв, много эмодзи, сленг типа 'имба', 'топ'.",
        "scientist": "Умный ученый: глубоко объясняет механику Minecraft с фактами.",
        "crazy": "Безумный профессор: энергичный, странный, с восклицаниями!",
        "minimalist": "Минималист: только суть, кратко и лаконично.",
        "storyteller": "Рассказчик: пишет о моде как о маленьком приключении.",
        "critic": "Строгий критик: находит и плюсы, и минусы мода.",
        "cheerleader": "Позитив: очень весело, призывает всех скачать мод.",
        "mystery": "Таинственный: интригует секретами мода.",
        "helper": "Помощник: фокус на том, как мод поможет в выживании.",
        "architect": "Архитектор: идеально для декоративных модов, про красоту.",
        "classic": "Классик: простой и понятный рекламный стиль.",
        "news": "Новости: журналистский стиль, официально и четко.",
        "friend": "Близкий друг: искренне, как будто советует другу.",
        "villager": "Житель: немного смешно, в стиле мира Minecraft.",
        "og": "OG Геймер: с ностальгией по старым версиям Minecraft."
    },
    "en": {
        "gamer": "Gamer style: drive, lots of emojis, slang like 'imba', 'top'.",
        "scientist": "Smart scientist: explains Minecraft mechanics in depth with facts.",
        "crazy": "Mad professor: energetic, a bit weird, with exclamations!",
        "minimalist": "Minimalist: only the core, short and concise.",
        "storyteller": "Storyteller: writes about the mod like a small adventure.",
        "critic": "Strict critic: finds both pros and cons of the mod.",
        "cheerleader": "Positive: very cheerful, encourages everyone to download.",
        "mystery": "Mysterious: intrigues with mod secrets.",
        "helper": "Helper: focus on how the mod helps in survival.",
        "architect": "Architect: perfect for decorative mods, about beauty.",
        "classic": "Classic: simple and clear advertising style.",
        "news": "News: journalistic style, official and clear.",
        "friend": "Close friend: sincere, as if advising a friend.",
        "villager": "Villager: a bit funny, Minecraft world style.",
        "og": "OG Gamer: with nostalgia for old Minecraft versions."
    }
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
    "ru": """Ты — креативный редактор Telegram-канала о модах для Minecraft.
Я передам тебе текст, а ты напиши пост в стиле [STYLE]. Уложись в 800 символов.
Пиши ТОЛЬКО на русском языке.

Стиль: [STYLE_DESC]

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
""",
    "en": """You are a creative editor for a Minecraft mods Telegram channel.
I will give you text, and you write a post in [STYLE] style. Keep it under 800 characters.
Write ONLY in English.

Style: [STYLE_DESC]

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

def generate_post(user_input, persona="gamer", lang="uz"):
    url = extract_url(user_input)
    site_context = ""
    
    if url:
        page_text = fetch_page_content(url)
        site_context = f"\n\nИнформация с сайта:\n{page_text}"

    selected_prompt = PROMPTS.get(lang, PROMPTS["uz"])
    persona_info = PERSONAS.get(lang, PERSONAS["uz"]).get(persona, PERSONAS["uz"]["gamer"])
    
    final_prompt = selected_prompt.replace("[STYLE]", persona).replace("[STYLE_DESC]", persona_info)
    final_prompt += f"\n\nСырая информация от пользователя:\n{user_input}{site_context}"
    
    response = client.models.generate_content(model=MODEL_ID, contents=final_prompt)
    
    final_text = response.text.strip()
    final_text = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', final_text)
    return final_text

def rewrite_post(text, style="fun"):
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
