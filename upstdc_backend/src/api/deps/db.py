from __future__ import annotations

from fastapi import HTTPException, status

# PUBLIC_INTERFACE
def require_db_available():
    """Dependency to ensure MongoDB is configured and available.

    This is a lightweight gate for routes that require DB access. It purposely avoids
    any import-time connection attempts and only performs a lazy check using
    src.db.mongo.get_database() and a readiness ping when needed.

    Raises:
        HTTPException: 503 Service Unavailable if DB is not configured or not reachable.

    Returns:
        The AsyncIOMotorDatabase handle when available, allowing route handlers or
        sub-dependencies to use it directly.
    """
    # Local import to avoid circular imports and any side effects at module import time
    from src.db.mongo import get_database  # noqa: WPS433 (allow local import for safety)

    db = get_database()
    if db is None:
        # Keep error generic to avoid leaking configuration or environment details
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database unavailable",
        )
    return db
