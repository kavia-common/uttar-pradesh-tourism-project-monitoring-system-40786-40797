from __future__ import annotations

import logging
import os
from functools import lru_cache
from typing import List, Optional

from pydantic import BaseModel, Field
from dotenv import load_dotenv

# Load environment variables from .env if present
load_dotenv()

logger = logging.getLogger(__name__)


class Settings(BaseModel):
    """
    Application settings loaded from environment variables.

    Security:
    - Never log secret values or connection URIs.
    - This model centralizes configuration access and keeps DB/JWT optional at startup
      so the application can boot and expose /health even when env vars are missing.
    """

    # Database (optional at startup; warn-only if missing)
    MONGO_URI: Optional[str] = Field(default=None, description="MongoDB connection URI (mongodb or mongodb+srv)")
    MONGO_DB: Optional[str] = Field(default=None, description="MongoDB database name")

    # Auth (JWT secret is required only when using protected routes; app may start without it)
    JWT_SECRET: Optional[str] = Field(default=None, description="Secret key for signing JWT tokens")
    JWT_ALGORITHM: str = Field(default="HS256", description="JWT signing algorithm")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=60, description="Access token expiry in minutes")

    # CORS
    CORS_ALLOWED_ORIGINS: List[str] = Field(
        default_factory=lambda: ["*"],
        description="Comma-separated list of allowed origins for CORS",
    )

    # App meta
    APP_NAME: str = Field(default="UPSTDC Backend API", description="Application name")
    APP_VERSION: str = Field(default=os.getenv("APP_VERSION", "0.1.0"), description="Application version")

    @property
    def db_enabled(self) -> bool:
        """True if database config is present."""
        return bool(self.MONGO_URI and self.MONGO_DB)

    @property
    def auth_enabled(self) -> bool:
        """True if JWT auth can be used."""
        return bool(self.JWT_SECRET)

    @staticmethod
    def _parse_origins(raw: Optional[str]) -> List[str]:
        if not raw or raw.strip() == "":
            return ["*"]
        return [o.strip() for o in raw.split(",") if o.strip()]

    @classmethod
    def from_env(cls) -> "Settings":
        """
        Build Settings from environment variables without failing on missing DB/JWT.
        Logs concise warnings when optional env is not configured.
        """
        cors_raw = os.getenv("CORS_ALLOWED_ORIGINS", "")
        settings = cls(
            MONGO_URI=os.getenv("MONGO_URI"),
            MONGO_DB=os.getenv("MONGO_DB"),
            JWT_SECRET=os.getenv("JWT_SECRET"),
            JWT_ALGORITHM=os.getenv("JWT_ALGORITHM", "HS256"),
            ACCESS_TOKEN_EXPIRE_MINUTES=int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60")),
            CORS_ALLOWED_ORIGINS=cls._parse_origins(cors_raw),
            APP_NAME=os.getenv("APP_NAME", "UPSTDC Backend API"),
            APP_VERSION=os.getenv("APP_VERSION", "0.1.0"),
        )

        # Warnings (no secrets included)
        if not settings.db_enabled:
            logger.warning("Database configuration not found. DB-dependent endpoints will return 503 until configured.")
        if not settings.auth_enabled:
            logger.warning("JWT secret not configured. Authentication features may be disabled or fail at runtime.")

        return settings


# PUBLIC_INTERFACE
@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return cached application Settings loaded from environment.

    This function should be used across the application to access configuration.
    """
    return Settings.from_env()
