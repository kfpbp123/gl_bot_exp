# core/config.py
import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import SecretStr, PostgresDsn, RedisDsn
from typing import List
from pathlib import Path

# Определяем путь к .env относительно этого файла
BASE_DIR = Path(__file__).resolve().parent.parent

class Settings(BaseSettings):
    # Bot Settings
    BOT_TOKEN: SecretStr
    ADMIN_IDS: List[int] = []
    
    # Database Settings
    DATABASE_URL: PostgresDsn
    
    # Redis Settings
    REDIS_URL: RedisDsn
    
    # AI Settings
    GEMINI_API_KEY: SecretStr
    
    # Path Settings
    WATERMARK_PATH: str = "assets/watermark.png"
    
    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env", 
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()
