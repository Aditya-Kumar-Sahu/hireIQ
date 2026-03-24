"""Application configuration via Pydantic Settings."""

from __future__ import annotations

from pydantic import field_validator
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

    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    REDIS_URL: str = "redis://localhost:6379/0"

    GEMINI_API_KEY: str = ""
    GOOGLE_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini/gemini-2.0-flash"
    GEMINI_EMBEDDING_MODEL: str = "gemini-embedding-001"
    GEMINI_EMBEDDING_DIMENSION: int = 1536

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
        "http://localhost:3100",
        "http://127.0.0.1:3100",
    ]

    @property
    def resolved_gemini_api_key(self) -> str:
        """Return the Gemini API key, accepting Google's alternate env var too."""
        return self.GEMINI_API_KEY or self.GOOGLE_API_KEY

    @field_validator("JWT_SECRET_KEY")
    @classmethod
    def jwt_secret_must_be_strong(cls, value: str) -> str:
        """Require a strong JWT secret so the app cannot boot with a public default."""
        if len(value.strip()) < 32:
            raise ValueError("JWT_SECRET_KEY must be at least 32 characters")
        return value


settings = Settings()
