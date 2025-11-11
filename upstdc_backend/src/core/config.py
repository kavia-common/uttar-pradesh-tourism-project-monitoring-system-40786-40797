from __future__ import annotations

import os
from functools import lru_cache
from typing import List, Optional

from pydantic import BaseModel, Field, ValidationError
from dotenv import load_dotenv

# Load environment variables from .env if present
load_dotenv()


class Settings(BaseModel):
    """
    Application settings loaded from environment variables.

    Security: Do not log secrets. Use this model to validate and access config safely.
    """

    # Database
    MONGO_URI: str = Field(..., description="MongoDB connection URI (mongodb or mongodb+srv)")
    MONGO_DB: str = Field(..., description="MongoDB database name")

    # Auth
    JWT_SECRET: str = Field(..., description="Secret key for signing JWT tokens")
    JWT_ALGORITHM: str = Field(default="HS256", description="JWT signing algorithm")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=60, description="Access token expiry in minutes")

    # CORS
    CORS_ALLOWED_ORIGINS: List[str] = Field(default_factory=lambda: ["*"],
                                            description="Comma-separated list of allowed origins for CORS")

    # App meta
    APP_NAME: str = Field(default="UPSTDC Backend API", description="Application name")
    APP_VERSION: str = Field(default=os.getenv("APP_VERSION", "0.1.0"), description="Application version")

    @staticmethod
    def _parse_origins(raw: Optional[str]) -> List[str]:
        if not raw or raw.strip() == "":
            return ["*"]
        # Split by comma and strip whitespace
        return [o.strip() for o in raw.split(",") if o.strip()]

    @classmethod
    def from_env(cls) -> "Settings":
        """
        Build Settings from environment variables with minimal processing.
        """
        cors_raw = os.getenv("CORS_ALLOWED_ORIGINS", "")
        data = {
            "MONGO_URI": os.getenv("MONGO_URI"),
            "MONGO_DB": os.getenv("MONGO_DB"),
            "JWT_SECRET": os.getenv("JWT_SECRET"),
            "JWT_ALGORITHM": os.getenv("JWT_ALGORITHM", "HS256"),
            "ACCESS_TOKEN_EXPIRE_MINUTES": int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60")),
            "CORS_ALLOWED_ORIGINS": cls._parse_origins(cors_raw),
            "APP_NAME": os.getenv("APP_NAME", "UPSTDC Backend API"),
            "APP_VERSION": os.getenv("APP_VERSION", "0.1.0"),
        }
        try:
            return cls(**data)
        except ValidationError as e:
            # Keep message concise without leaking secrets
            missing = []
            for err in e.errors():
                loc = ".".join([str(x) for x in err.get("loc", [])])
                if err.get("type") == "missing":
                    missing.append(loc)
            # Raise a clear error to help setup; do not include secret values
            raise RuntimeError(
                "Required environment variables are missing or invalid: "
                + ", ".join(missing) if missing else str(e)
            ) from e


# PUBLIC_INTERFACE
@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return cached application Settings loaded from environment.

    This function should be used across the application to access configuration.
    """
    return Settings.from_env()
