"""Application configuration via Pydantic Settings."""

from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Central application settings, loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    APP_NAME: str = "HireIQ"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = False
    BACKEND_PUBLIC_URL: str = "http://localhost:8000"

    DATABASE_URL: str = "postgresql+asyncpg://hireiq:hireiq_secret@localhost:5432/hireiq"
    PGVECTOR_ENABLED: bool = True

    JWT_SECRET_KEY: str = "change-me-to-a-random-64-char-secret"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    REDIS_URL: str = "redis://localhost:6379/0"

    OPENAI_API_KEY: str = ""

    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    GOOGLE_REDIRECT_URI: str = "http://localhost:3000/api/auth/google/callback"
    GOOGLE_CALENDAR_ID: str = "primary"
    GOOGLE_CALENDAR_ACCESS_TOKEN: str = ""
    GOOGLE_CALENDAR_REFRESH_TOKEN: str = ""
    GOOGLE_CALENDAR_TOKEN_URI: str = "https://oauth2.googleapis.com/token"
    GOOGLE_OAUTH_AUTHORIZE_URI: str = "https://accounts.google.com/o/oauth2/v2/auth"

    RESEND_API_KEY: str = ""
    FROM_EMAIL: str = "noreply@hireiq.dev"

    R2_ACCOUNT_ID: str = ""
    R2_ACCESS_KEY_ID: str = ""
    R2_SECRET_ACCESS_KEY: str = ""
    R2_BUCKET_NAME: str = "hireiq-resumes"
    R2_ENDPOINT_URL: str = ""
    R2_REGION: str = "auto"

    ATS_WEBHOOK_SECRET: str = ""
    ATS_WEBHOOK_PROVIDER: str = "greenhouse"

    ALLOWED_ORIGINS: list[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]


settings = Settings()
