# pyrefly: ignore [missing-import]
from pydantic_settings import BaseSettings
from typing import List
from pathlib import Path


def _find_env_file() -> str:
    """Search for .env from CWD upward so the server can be launched
    from either the project root or apps/backend/ without issues."""
    cwd = Path.cwd()
    candidates = [
        cwd / ".env",                       # launched from project root
        cwd.parent / ".env",                # launched from apps/backend
        cwd.parent.parent / ".env",         # launched from apps/backend/app
        Path(__file__).parent.parent.parent.parent / ".env",  # absolute fallback
    ]
    for p in candidates:
        if p.is_file():
            return str(p)
    return ".env"  # pydantic-settings default


class Settings(BaseSettings):
    # ── App ──────────────────────────────────────
    APP_NAME: str = "OrchestAI"
    APP_ENV: str = "development"
    APP_DEBUG: bool = True
    APP_HOST: str = "0.0.0.0"
    APP_PORT: int = 8000
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:3001"

    # ── Database ──────────────────────────────────
    DATABASE_URL: str = "postgresql://orchestai:orchestai_pass@localhost:5432/orchestai_db"

    # ── Redis ─────────────────────────────────────
    REDIS_URL: str = "redis://localhost:6379/0"

    # ── JWT ───────────────────────────────────────
    JWT_SECRET: str = "change-this-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 30

    # ── OpenAI ────────────────────────────────────
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4o-mini"
    OPENAI_EMBEDDING_MODEL: str = "text-embedding-3-small"
    # Set true to skip real OpenAI calls (no API key needed for local demo)
    AI_MOCK_MODE: bool = True

    # ── Email ─────────────────────────────────────
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM: str = "noreply@orchestai.com"

    # ── Celery (optional) ─────────────────────────
    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/2"

    @property
    def cors_origins_list(self) -> List[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",")]

    class Config:
        env_file = _find_env_file()
        case_sensitive = True


settings = Settings()
