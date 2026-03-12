# core/config.py
import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import SecretStr, PostgresDsn, RedisDsn
from typing import List
from pathlib import Path

# Определяем путь к .env относительно этого файла
BASE_DIR = Path(__file__).resolve().parent.parent

from pydantic import SecretStr, PostgresDsn, RedisDsn, field_validator, AliasChoices, Field
from typing import List, Union, Any
from pathlib import Path
import json

# Определяем путь к .env относительно этого файла
BASE_DIR = Path(__file__).resolve().parent.parent

class Settings(BaseSettings):
    # Bot Settings (поддерживаем оба названия: новое и старое)
    BOT_TOKEN: SecretStr = Field(validation_alias=AliasChoices('BOT_TOKEN', 'TELEGRAM_TOKEN'))
    
    # Обработка ADMIN_IDS (принимает число, строку или список)
    ADMIN_IDS: List[int] = []

    @field_validator("ADMIN_IDS", mode="before")
    @classmethod
    def parse_admin_ids(cls, v: Any) -> List[int]:
        if isinstance(v, int):
            return [v]
        if isinstance(v, str):
            try:
                # Пробуем распарсить как JSON список [123, 456]
                data = json.loads(v)
                return data if isinstance(data, list) else [int(data)]
            except:
                # Если не JSON, пробуем как строку через запятую "123,456"
                return [int(i.strip()) for i in v.split(",") if i.strip().isdigit()]
        return v
    
    # Database Settings
    DATABASE_URL: Union[PostgresDsn, str]

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def fix_database_url(cls, v: Any) -> str:
        if isinstance(v, str):
            # Заменяем postgres:// на postgresql:// (для совместимости)
            if v.startswith("postgres://"):
                v = v.replace("postgres://", "postgresql://", 1)
            # Добавляем +asyncpg если его нет
            if v.startswith("postgresql://"):
                v = v.replace("postgresql://", "postgresql+asyncpg://", 1)
        return v
    
    # Redis Settings
    REDIS_URL: RedisDsn
    
    # AI Settings
    GEMINI_API_KEY: SecretStr = Field(validation_alias=AliasChoices('GEMINI_API_KEY', 'GEMINI_KEY'))
    
    # Path Settings
    WATERMARK_PATH: str = "assets/watermark.png"
    
    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env" if (BASE_DIR / ".env").exists() else None,
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()
