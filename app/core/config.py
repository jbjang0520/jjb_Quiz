import os
from pydantic_settings import BaseSettings
from typing import List, Optional

class Settings(BaseSettings):
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "FastAPI Quiz System"

    POSTGRES_SERVER: str
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str
    SQLALCHEMY_DATABASE_URI: Optional[str] = None

    BACKEND_CORS_ORIGINS: List[str] = []

    REDIS_HOST: str
    REDIS_PORT: int = 6379

    ACCESS_TOKEN_EXPIRE_MINUTES: int = 720  # 나중에 기본값 60분 으로 변경
    SECRET_KEY: str

    class Config:
        env_file = ".env"
        extra = "ignore"

    @property
    def get_postgres_server(self) -> str:
        if os.getenv("IS_DOCKER", "").lower() == "true":
            return self.POSTGRES_SERVER
        return "localhost"

settings = Settings()

if settings.SQLALCHEMY_DATABASE_URI is None:
    postgres_server = settings.get_postgres_server
    settings.SQLALCHEMY_DATABASE_URI = (
        f"postgresql://{settings.POSTGRES_USER}:{settings.POSTGRES_PASSWORD}"
        f"@{postgres_server}:5432/{settings.POSTGRES_DB}"
    )