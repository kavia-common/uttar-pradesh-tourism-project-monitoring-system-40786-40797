from __future__ import annotations

import logging
from typing import Optional

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from fastapi import FastAPI

from src.core.config import get_settings

logger = logging.getLogger(__name__)

_client: Optional[AsyncIOMotorClient] = None


def _can_use_db() -> bool:
    settings = get_settings()
    return settings.db_enabled


def _ensure_client() -> Optional[AsyncIOMotorClient]:
    """Create the Mongo client lazily only if DB is enabled."""
    global _client
    if not _can_use_db():
        return None
    if _client is None:
        settings = get_settings()
        # Do not log URI or any secrets
        _client = AsyncIOMotorClient(settings.MONGO_URI)  # type: ignore[arg-type]
    return _client


# PUBLIC_INTERFACE
def get_database() -> Optional[AsyncIOMotorDatabase]:
    """Return a handle to the configured MongoDB database, or None if DB is disabled."""
    settings = get_settings()
    client = _ensure_client()
    if client is None or not settings.db_enabled:
        return None
    return client[settings.MONGO_DB]  # type: ignore[index]


# PUBLIC_INTERFACE
async def check_db_ready() -> tuple[bool, Optional[str]]:
    """Ping MongoDB to verify readiness when enabled.

    Returns:
        (True, None) if DB is configured and reachable.
        (False, reason) if DB is configured but not reachable; or disabled.
    """
    if not _can_use_db():
        return False, "Database configuration not provided"
    client = _ensure_client()
    if client is None:
        return False, "Database client not initialized"
    try:
        await client.admin.command("ping")
        return True, None
    except Exception as exc:
        # Do not include sensitive details; keep concise
        logger.warning("Database ping failed; service will report not ready.")
        return False, f"Database not reachable: {exc.__class__.__name__}"


def register_mongo_events(app: FastAPI) -> None:
    """No-op registration retained for compatibility.

    We avoid forcing DB connection at startup; cleanup on shutdown if created.
    """

    @app.on_event("shutdown")
    async def _close_client() -> None:
        global _client
        try:
            if _client is not None:
                _client.close()
        finally:
            _client = None
