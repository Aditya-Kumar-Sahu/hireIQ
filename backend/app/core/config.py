"""
Application configuration via Pydantic Settings.

All environment variables are loaded from `.env` at the project root.
Defaults are provided for local development; override in production via
environment variables or a production `.env` file.
"""

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

    # ── App ────────────────────────────────────────────────────────────
    APP_NAME: str = "HireIQ"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = False

    # ── Database ───────────────────────────────────────────────────────
    DATABASE_URL: str = "postgresql+asyncpg://hireiq:hireiq_secret@localhost:5432/hireiq"
    PGVECTOR_ENABLED: bool = True

    # ── Authentication ─────────────────────────────────────────────────
    JWT_SECRET_KEY: str = "change-me-to-a-random-64-char-secret"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # ── Redis ──────────────────────────────────────────────────────────
    REDIS_URL: str = "redis://localhost:6379/0"

    # ── OpenAI ─────────────────────────────────────────────────────────
    OPENAI_API_KEY: str = ""

    # ── Google Calendar ────────────────────────────────────────────────
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    GOOGLE_REDIRECT_URI: str = "http://localhost:3000/api/auth/google/callback"
    GOOGLE_CALENDAR_ID: str = "primary"
    GOOGLE_CALENDAR_ACCESS_TOKEN: str = ""
    GOOGLE_CALENDAR_REFRESH_TOKEN: str = ""
    GOOGLE_CALENDAR_TOKEN_URI: str = "https://oauth2.googleapis.com/token"

    # ── Email (Resend) ─────────────────────────────────────────────────
    RESEND_API_KEY: str = ""
    FROM_EMAIL: str = "noreply@hireiq.dev"

    # ── Cloud Storage (Cloudflare R2) ──────────────────────────────────
    R2_ACCOUNT_ID: str = ""
    R2_ACCESS_KEY_ID: str = ""
    R2_SECRET_ACCESS_KEY: str = ""
    R2_BUCKET_NAME: str = "hireiq-resumes"

    # ── CORS ───────────────────────────────────────────────────────────
    ALLOWED_ORIGINS: list[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]


# Singleton settings instance — import this everywhere.
settings = Settings()
