import logging
import sys
from typing import List, Optional
from pydantic_settings import BaseSettings
from pydantic import validator

logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    PROJECT_NAME: str = "Handball Manager API"
    VERSION: str = "1.0.0"
    DESCRIPTION: str = "API for managing handball clubs, teams, players, games, and events"

    # Database
    DATABASE_URL: str = "postgresql://postgres:postgres@db:5432/handball_manager"

    # Security
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # CORS - loaded from CORS_ORIGINS env var (comma-separated), with localhost defaults for dev
    BACKEND_CORS_ORIGINS: List[str] = [
        "http://localhost",
        "http://localhost:3000",
        "http://localhost:5173",
    ]

    @validator("BACKEND_CORS_ORIGINS", pre=True)
    def assemble_cors_origins(cls, v):
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v

    # Frontend URL (used for redirects, email links, etc.)
    FRONTEND_URL: str = "http://localhost:5173"

    # Redis (for caching and WebSocket pub/sub in production)
    REDIS_URL: Optional[str] = None

    # OAuth (optional)
    GOOGLE_CLIENT_ID: Optional[str] = None
    GOOGLE_CLIENT_SECRET: Optional[str] = None
    APPLE_CLIENT_ID: Optional[str] = None

    # Email (SMTP) Configuration
    SMTP_HOST: Optional[str] = None
    SMTP_PORT: int = 587
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    SMTP_FROM_EMAIL: str = "noreply@handball-manager.de"
    SMTP_FROM_NAME: str = "Handball Manager"
    SMTP_USE_TLS: bool = True
    SMTP_USE_SSL: bool = False

    # Email Dry-Run Mode (for development - logs instead of sending)
    EMAIL_DRY_RUN: bool = True

    # Cookie auth (#42). The deployed frontend + backend live on different
    # Cloud Run hostnames, so `SameSite=Lax` would prevent cookies from
    # attaching to cross-origin XHR. Production must use `None` + `Secure`
    # (HTTPS-only); local dev defaults to `Lax` over HTTP so logins work
    # against http://localhost. Override AUTH_COOKIE_SAMESITE / SECURE
    # explicitly when serving on a single domain.
    AUTH_COOKIE_NAME_ACCESS: str = "access_token"
    AUTH_COOKIE_NAME_REFRESH: str = "refresh_token"
    AUTH_COOKIE_NAME_CSRF: str = "csrf_token"
    AUTH_COOKIE_SAMESITE: str = "lax"   # "lax" | "strict" | "none"
    AUTH_COOKIE_SECURE: bool = False    # True in prod (HTTPS only)
    AUTH_COOKIE_DOMAIN: Optional[str] = None  # set when serving multi-subdomain on one site

    # Sentry observability (#64). Leave SENTRY_DSN unset to disable.
    # SENTRY_RELEASE is populated by Cloud Build with $SHORT_SHA so each
    # deploy is tagged — bisecting "which deploy introduced this" works.
    SENTRY_DSN: Optional[str] = None
    SENTRY_ENVIRONMENT: str = "development"
    SENTRY_RELEASE: Optional[str] = None
    SENTRY_TRACES_SAMPLE_RATE: float = 0.1  # 10% of requests get perf spans

    class Config:
        env_file = ".env"
        case_sensitive = True

    def validate_required_secrets(self) -> None:
        """Fail fast if required secrets are missing or still set to defaults."""
        errors: list[str] = []
        if not self.DATABASE_URL:
            errors.append("DATABASE_URL is required")
        if not self.SECRET_KEY or self.SECRET_KEY == "your-secret-key-change-in-production":
            errors.append(
                "SECRET_KEY must be set to a secure value (not the default)"
            )
        if errors:
            for err in errors:
                logger.error("CONFIG ERROR: %s", err)
            raise SystemExit(
                "Missing required configuration. Set the environment variables listed above."
            )


settings = Settings()
