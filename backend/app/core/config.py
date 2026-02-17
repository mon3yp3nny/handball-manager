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
