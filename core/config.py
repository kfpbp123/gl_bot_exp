# core/config.py
import json
from pathlib import Path
from typing import List, Union, Any

from pydantic import SecretStr, PostgresDsn, RedisDsn, Field, AliasChoices, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Определяем путь к .env относительно этого файла
BASE_DIR = Path(__file__).resolve().parent.parent

class Settings(BaseSettings):
    # Bot Settings
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
                data = json.loads(v)
                return data if isinstance(data, list) else [int(data)]
            except:
                return [int(i.strip()) for i in v.split(",") if i.strip().isdigit()]
        return v
    
    # Database Settings
    DATABASE_URL: Union[PostgresDsn, str]

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def fix_database_url(cls, v: Any) -> str:
        if isinstance(v, str):
            if v.startswith("postgres://"):
                v = v.replace("postgres://", "postgresql://", 1)
            if v.startswith("postgresql://") and "+asyncpg" not in v:
                v = v.replace("postgresql://", "postgresql+asyncpg://", 1)
        return v
    
    # Redis Settings
    REDIS_URL: RedisDsn
    
    # AI Settings
    GEMINI_API_KEY: SecretStr = Field(validation_alias=AliasChoices('GEMINI_API_KEY', 'GEMINI_KEY'))
    
    # Scheduling Settings
    SMART_QUEUE_INTERVAL_HOURS: int = 8
    
    # Channel Settings
    CHANNELS: List[str] = ["@lazikosmods"]
    
    @field_validator("CHANNELS", mode="before")
    @classmethod
    def parse_channels(cls, v: Any) -> List[str]:
        if isinstance(v, str):
            if v.startswith("["):
                try:
                    return json.loads(v)
                except:
                    pass
            return [ch.strip() for ch in v.split(",") if ch.strip()]
        return v
    
    # Path Settings
    WATERMARK_PATH: str = "assets/watermark.png"
    
    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env" if (BASE_DIR / ".env").exists() else None,
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()
