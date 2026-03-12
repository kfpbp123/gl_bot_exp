# core/config.py
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import SecretStr, PostgresDsn, RedisDsn
from typing import List

class Settings(BaseSettings):
    # Bot Settings
    BOT_TOKEN: SecretStr
    ADMIN_IDS: List[int] = []
    
    # Database Settings
    # postgresql+asyncpg://user:pass@localhost:5432/dbname
    DATABASE_URL: PostgresDsn
    
    # Redis Settings
    # redis://localhost:6379/0
    REDIS_URL: RedisDsn
    
    # AI Settings
    GEMINI_API_KEY: SecretStr
    
    # Path Settings
    WATERMARK_PATH: str = "assets/watermark.png"
    
    model_config = SettingsConfigDict(
        env_file=".env", 
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()
