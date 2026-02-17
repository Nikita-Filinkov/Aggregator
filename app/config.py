import os
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    BASE_URL: str
    LMS_API_KEY: str
    LOG_LEVEL: str = "INFO"

    POSTGRES_DATABASE_NAME: str
    POSTGRES_HOST: str
    POSTGRES_PASSWORD: str
    POSTGRES_PORT: int
    POSTGRES_USER: Optional[str] = None

    POSTGRES_CONNECTION_STRING: Optional[str] = None

    model_config = SettingsConfigDict(
        env_file_encoding="utf-8",
        extra="ignore",
    )

    def __init__(self, **data):
        super().__init__(**data)
        if not self.POSTGRES_CONNECTION_STRING:
            self.POSTGRES_CONNECTION_STRING = (
                f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
                f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DATABASE_NAME}"
            )
        else:
            if not self.POSTGRES_USER:
                parsed = urlparse(self.POSTGRES_CONNECTION_STRING)
                self.POSTGRES_USER = parsed.username
                if not self.POSTGRES_PASSWORD:
                    self.POSTGRES_PASSWORD = parsed.password
                if not self.POSTGRES_HOST:
                    self.POSTGRES_HOST = parsed.hostname
                if not self.POSTGRES_PORT:
                    self.POSTGRES_PORT = parsed.port or 5432
                if not self.POSTGRES_DATABASE_NAME:
                    self.POSTGRES_DATABASE_NAME = parsed.path.lstrip("/")


if os.getenv("DOCKER_ENV") == "true":
    settings = Settings()
else:
    env_file = os.path.join(Path(__file__).parent.parent, ".env.local")
    settings = Settings(_env_file=env_file)

print(settings.POSTGRES_CONNECTION_STRING)
