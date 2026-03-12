import sqlite3
import time

def init_db():
    conn = sqlite3.connect('bot_data.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS queue
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  photo_id TEXT,
                  text TEXT,
                  document_id TEXT,
                  status TEXT DEFAULT 'pending',
                  user_id INTEGER)''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (user_id INTEGER PRIMARY KEY,
                  username TEXT,
                  target_channel TEXT,
                  custom_logo TEXT,
                  registration_date INTEGER)''')
    
    # Безопасно добавляем новые колонки, если их нет
    try:
        c.execute("ALTER TABLE queue ADD COLUMN channel_id TEXT")
    except sqlite3.OperationalError:
        pass # Колонка уже существует
    
    try:
        c.execute("ALTER TABLE queue ADD COLUMN scheduled_time INTEGER")
    except sqlite3.OperationalError:
        pass # Колонка уже существует

    try:
        c.execute("ALTER TABLE queue ADD COLUMN user_id INTEGER")
    except sqlite3.OperationalError:
        pass
        
    conn.commit()
    conn.close()

def add_user(user_id, username, target_channel=None):
    conn = sqlite3.connect('bot_data.db')
    c = conn.cursor()
    current_time = int(time.time())
    c.execute("INSERT OR IGNORE INTO users (user_id, username, registration_date, target_channel) VALUES (?, ?, ?, ?)", 
              (user_id, username, current_time, target_channel))
    if target_channel:
        c.execute("UPDATE users SET target_channel = ? WHERE user_id = ?", (target_channel, user_id))
    conn.commit()
    conn.close()

def update_user_channel(user_id, channel):
    conn = sqlite3.connect('bot_data.db')
    c = conn.cursor()
    c.execute("UPDATE users SET target_channel = ? WHERE user_id = ?", (channel, user_id))
    conn.commit()
    conn.close()

def update_user_logo(user_id, logo_path):
    conn = sqlite3.connect('bot_data.db')
    c = conn.cursor()
    c.execute("UPDATE users SET custom_logo = ? WHERE user_id = ?", (logo_path, user_id))
    conn.commit()
    conn.close()

def get_user(user_id):
    conn = sqlite3.connect('bot_data.db')
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
    row = c.fetchone()
    conn.close()
    return row

def get_all_users():
    conn = sqlite3.connect('bot_data.db')
    c = conn.cursor()
    c.execute("SELECT * FROM users")
    rows = c.fetchall()
    conn.close()
    return rows

def add_to_queue(photo_id, text, document_id=None, channel_id=None, scheduled_time=None, user_id=None):
    conn = sqlite3.connect('bot_data.db')
    c = conn.cursor()
    c.execute("INSERT INTO queue (photo_id, text, document_id, channel_id, scheduled_time, user_id) VALUES (?, ?, ?, ?, ?, ?)", 
              (photo_id, text, document_id, channel_id, scheduled_time, user_id))
    conn.commit()
    conn.close()

def get_ready_posts():
    """Получает посты, время публикации которых уже наступило"""
    conn = sqlite3.connect('bot_data.db')
    c = conn.cursor()
    current_time = int(time.time())
    # Выбираем посты, где время <= текущему, или время не задано (сразу в очередь)
    c.execute('''SELECT id, photo_id, text, document_id, channel_id 
                 FROM queue 
                 WHERE status='pending' AND (scheduled_time IS NULL OR scheduled_time <= ?) 
                 ORDER BY scheduled_time ASC''', (current_time,))
    rows = c.fetchall()
    conn.close()
    return rows

def mark_as_posted(post_id):
    conn = sqlite3.connect('bot_data.db')
    c = conn.cursor()
    c.execute("UPDATE queue SET status='posted' WHERE id=?", (post_id,))
    conn.commit()
    conn.close()

def get_queue_count():
    conn = sqlite3.connect('bot_data.db')
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM queue WHERE status='pending'")
    count = c.fetchone()[0]
    conn.close()
    return count

def get_all_pending():
    conn = sqlite3.connect('bot_data.db')
    c = conn.cursor()
    c.execute("SELECT id, photo_id, text, document_id, channel_id, scheduled_time FROM queue WHERE status='pending' ORDER BY scheduled_time ASC")
    rows = c.fetchall()
    conn.close()
    return rows

def delete_from_queue(post_id):
    conn = sqlite3.connect('bot_data.db')
    c = conn.cursor()
    c.execute("DELETE FROM queue WHERE id=?", (post_id,))
    conn.commit()
    conn.close()

def get_last_scheduled_time():
    """Находит время самого последнего запланированного поста в очереди."""
    conn = sqlite3.connect('bot_data.db')
    c = conn.cursor()
    c.execute("SELECT scheduled_time FROM queue WHERE status='pending' AND scheduled_time IS NOT NULL ORDER BY scheduled_time DESC LIMIT 1")
    result = c.fetchone()
    conn.close()
    return result[0] if result else None

def get_admin_stats():
    """Собирает общую статистику для админа"""
    conn = sqlite3.connect('bot_data.db')
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM queue")
    total = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM queue WHERE status='posted'")
    published = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM queue WHERE status='pending'")
    queue_count = c.fetchone()[0]
    conn.close()
    return {'total': total, 'published': published, 'queue': queue_count}

def get_user_stats(user_id):
    """Собирает статистику для конкретного пользователя"""
    import pytz
    from datetime import datetime
    
    conn = sqlite3.connect('bot_data.db')
    c = conn.cursor()
    
    # Всего постов пользователя
    c.execute("SELECT COUNT(*) FROM queue WHERE user_id = ?", (user_id,))
    total = c.fetchone()[0]
    
    # Опубликовано пользователем
    c.execute("SELECT COUNT(*) FROM queue WHERE user_id = ? AND status='posted'", (user_id,))
    published = c.fetchone()[0]
    
    # В очереди у пользователя
    c.execute("SELECT COUNT(*) FROM queue WHERE user_id = ? AND status='pending'", (user_id,))
    queue_count = c.fetchone()[0]
    
    # Активность пользователя за сегодня
    tashkent_tz = pytz.timezone('Asia/Tashkent')
    today_start = int(datetime.now(tashkent_tz).replace(hour=0, minute=0, second=0, microsecond=0).timestamp())
    c.execute("SELECT COUNT(*) FROM queue WHERE user_id = ? AND scheduled_time >= ?", (user_id, today_start))
    today = c.fetchone()[0]
    
    conn.close()
    return {
        'total': total,
        'published': published,
        'queue': queue_count,
        'today': today
    }

def get_all_posts():
    """Выгружает все посты для бэкапа"""
    conn = sqlite3.connect('bot_data.db')
    c = conn.cursor()
    c.execute("SELECT * FROM queue")
    rows = c.fetchall()
    conn.close()
    return rows

def record_published_post(photo_id, text, document_id, channel_id):
    """Записывает пост сразу как 'posted', чтобы он учитывался в статистике"""
    import sqlite3
    import time
    conn = sqlite3.connect('bot_data.db')
    c = conn.cursor()
    current_time = int(time.time())
    c.execute("INSERT INTO queue (photo_id, text, document_id, channel_id, scheduled_time, status) VALUES (?, ?, ?, ?, ?, 'posted')", 
              (photo_id, text, document_id, channel_id, current_time))
    conn.commit()
    conn.close()

# --- ФУНКЦИИ ДЛЯ АНАЛИЗА КОММЕНТАРИЕВ ---

def init_comments_table():
    conn = sqlite3.connect('bot_data.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS comments
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  user_name TEXT,
                  text TEXT,
                  timestamp INTEGER)''')
    conn.commit()
    conn.close()

def save_comment(user_name, text, timestamp):
    conn = sqlite3.connect('bot_data.db')
    c = conn.cursor()
    c.execute("INSERT INTO comments (user_name, text, timestamp) VALUES (?, ?, ?)", 
              (user_name, text, timestamp))
    conn.commit()
    conn.close()

def get_all_comments():
    conn = sqlite3.connect('bot_data.db')
    c = conn.cursor()
    c.execute("SELECT user_name, text FROM comments ORDER BY timestamp ASC")
    rows = c.fetchall()
    conn.close()
    return rows

def clear_comments():
    conn = sqlite3.connect('bot_data.db')
    c = conn.cursor()
    c.execute("DELETE FROM comments")
    conn.commit()
    conn.close()

# Вызываем создание таблицы комментариев при импорте
init_comments_table()
