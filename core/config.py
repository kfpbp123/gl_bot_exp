# core/config.py
import json
from pathlib import Path
from typing import List, Union, Any, Optional

from pydantic import SecretStr, PostgresDsn, RedisDsn, Field, AliasChoices, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Определяем путь к .env относительно этого файла
BASE_DIR = Path(__file__).resolve().parent.parent

class Settings(BaseSettings):
    # Bot Settings
    BOT_TOKEN: SecretStr = Field(validation_alias=AliasChoices('BOT_TOKEN', 'TELEGRAM_TOKEN'))
    
    # Обработка ADMIN_IDS (принимает число, строку или список)
    ADMIN_IDS: Any = Field(default_factory=list)

    @field_validator("ADMIN_IDS", mode="before")
    @classmethod
    def parse_admin_ids(cls, v: Any) -> List[int]:
        if isinstance(v, int):
            return [v]
        if isinstance(v, str) and v.strip():
            try:
                data = json.loads(v)
                return data if isinstance(data, list) else [int(data)]
            except:
                return [int(i.strip()) for i in v.split(",") if i.strip().isdigit()]
        if isinstance(v, list):
            return [int(i) for i in v]
        return []
    
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
        return str(v)
    
    # Redis Settings
    REDIS_URL: Union[RedisDsn, str]
    
    # AI Settings
    GEMINI_API_KEY: SecretStr = Field(validation_alias=AliasChoices('GEMINI_API_KEY', 'GEMINI_KEY'))
    
    # Scheduling Settings
    SMART_QUEUE_INTERVAL_HOURS: int = 8
    
    # Channel Settings - Используем Any для обхода строгой проверки типа на этапе загрузки из env
    CHANNELS: Any = Field(default_factory=lambda: ["@lazikosmods"])
    
    @field_validator("CHANNELS", mode="before")
    @classmethod
    def parse_channels(cls, v: Any) -> List[str]:
        if not v:
            return ["@lazikosmods"]
        if isinstance(v, str):
            v = v.strip()
            if v.startswith("["):
                try:
                    data = json.loads(v)
                    if isinstance(data, list):
                        return [str(ch).strip() for ch in data if ch]
                except:
                    pass
            # Если это просто строка через запятую или одно название
            return [ch.strip() for ch in v.split(",") if ch.strip()]
        if isinstance(v, list):
            return [str(ch).strip() for ch in v if ch]
        return ["@lazikosmods"]
    
    # Path Settings
    WATERMARK_PATH: str = "assets/watermark.png"
    
    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env" if (BASE_DIR / ".env").exists() else None,
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()
