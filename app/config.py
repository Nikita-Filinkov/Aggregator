import os
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    BASE_URL: str = "http://events-provider.dev-1.python-labs.ru/"
    LMS_API_KEY: str

    model_config = SettingsConfigDict(
        env_file=os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".env"),
        extra="ignore",
    )


settings = Settings()
