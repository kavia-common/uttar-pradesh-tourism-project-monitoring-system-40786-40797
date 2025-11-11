from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncGenerator, Optional

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from fastapi import FastAPI

from src.core.config import get_settings

_client: Optional[AsyncIOMotorClient] = None


def get_client() -> AsyncIOMotorClient:
    """
    Internal accessor for the singleton AsyncIOMotorClient.
    This should be initialized via register_mongo_events during app startup.
    """
    global _client
    if _client is None:
        # Lazy initialization as fallback (still recommended to use startup hook)
        settings = get_settings()
        _client = AsyncIOMotorClient(settings.MONGO_URI)
    return _client


# PUBLIC_INTERFACE
def get_database() -> AsyncIOMotorDatabase:
    """Return a handle to the configured MongoDB database."""
    settings = get_settings()
    client = get_client()
    return client[settings.MONGO_DB]


@asynccontextmanager
async def _lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Lifespan context manager to initialize and cleanup MongoDB client.
    """
    global _client
    settings = get_settings()
    _client = AsyncIOMotorClient(settings.MONGO_URI)

    try:
        # optional: ping to verify connectivity (non-fatal if it fails later)
        await _client.admin.command("ping")
    except Exception:
        # We deliberately avoid raising here to allow app to start,
        # but the first DB usage will surface the error.
        pass

    try:
        yield
    finally:
        if _client is not None:
            _client.close()
            _client = None


# PUBLIC_INTERFACE
def register_mongo_events(app: FastAPI) -> None:
    """Register startup/shutdown handlers for MongoDB Motor client on the FastAPI app.

    This sets app.router.lifespan_context to ensure client is managed automatically.
    """
    app.router.lifespan_context = _lifespan  # type: ignore[assignment]
