import pytz
from datetime import datetime, timedelta
import re

def get_time_greeting():
    tashkent_tz = pytz.timezone('Asia/Tashkent')
    hour = datetime.now(tashkent_tz).hour
    if hour < 6: return "🌙 Доброй ночи"
    elif hour < 12: return "🌅 Доброе утро"
    elif hour < 18: return "☀️ Добрый день"
    else: return "🌆 Добрый вечер"

def format_queue_post(post, index, total):
    post_id, photo_id, text, doc_id, channel, time_sched = post[:6]
    type_icon = "🖼️" if photo_id else "📝" if not doc_id else "📁"
    if photo_id and ',' in photo_id: type_icon = "📚"
    
    tashkent_tz = pytz.timezone('Asia/Tashkent')
    if time_sched:
        dt = datetime.fromtimestamp(time_sched, tashkent_tz)
        now = datetime.now(tashkent_tz)
        if dt.date() == now.date(): time_str = f"Сегодня в {dt.strftime('%H:%M')}"
        elif dt.date() == (now + timedelta(days=1)).date(): time_str = f"Завтра в {dt.strftime('%H:%M')}"
        else: time_str = dt.strftime('%d.%m.%Y %H:%M')
    else:
        time_str = "⏰ Не запланировано"
        
    preview = re.sub(r'<[^>]+>', '', text)[:100]
    return f"""╔═══📋 ПОСТ {index}/{total} ═══╗
{type_icon} <b>Тип:</b> {'Альбом' if photo_id and ',' in photo_id else 'Фото' if photo_id else 'Текст'}
📢 <b>Канал:</b> {channel}
⏰ <b>Время:</b> {time_str}

📝 <b>Превью:</b>
<i>{preview}{'...' if len(text) > 100 else ''}</i>
╚════════════════════╝"""
