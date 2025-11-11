from typing import List

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware

from src.core.config import get_settings
from src.db.mongo import register_mongo_events, check_db_ready

settings = get_settings()

openapi_tags = [
    {"name": "Health", "description": "Service health and readiness endpoints"},
]

app = FastAPI(
    title=settings.APP_NAME,
    description="UPSTDC Project Monitoring System Backend APIs",
    version=settings.APP_VERSION,
    contact={"name": "UPSTDC Backend", "url": "https://upstdc.gov.in"},
    license_info={"name": "Proprietary"},
    openapi_tags=openapi_tags,
)

# Avoid mandatory DB connect at startup, but keep graceful shutdown
register_mongo_events(app)

# Configure CORS from environment
allowed_origins: List[str] = settings.CORS_ALLOWED_ORIGINS or ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# PUBLIC_INTERFACE
def require_db_available():
    """Dependency that ensures the database is configured and available.

    Raises:
        HTTPException 503 if DB is not configured or not reachable.
    """
    from src.db.mongo import get_database  # local import to avoid cyc deps
    db = get_database()
    if db is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database not available",
        )
    return db


# PUBLIC_INTERFACE
@app.get(
    "/health",
    summary="Health",
    description="Liveness probe for the service. Always returns UP when the process is running.",
    tags=["Health"],
)
def health() -> dict:
    """Liveness endpoint.

    Returns:
        JSON object with status field only to avoid leaking configuration.
    """
    return {"status": "UP"}


# PUBLIC_INTERFACE
@app.get(
    "/ready",
    summary="Readiness",
    description="Readiness probe. Returns READY only when the MongoDB connection is configured and reachable.",
    tags=["Health"],
    responses={
        200: {"description": "Service ready"},
        503: {"description": "Service not ready or degraded"},
    },
)
async def ready() -> dict:
    """Readiness endpoint checking MongoDB connectivity if configured.

    Returns:
        200 JSON {status: READY} if DB is configured and reachable.
        503 JSON {status: DEGRADED, reason: ...} otherwise.
    """
    ok, reason = await check_db_ready()
    if ok:
        return {"status": "READY"}
    raise HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail={"status": "DEGRADED", "reason": reason},
    )


# PUBLIC_INTERFACE
@app.get(
    "/",
    summary="Root Health (legacy)",
    description="Legacy root endpoint. Mirrors /health for backward compatibility.",
    tags=["Health"],
)
def root_health() -> dict:
    """Legacy root health endpoint."""
    return {"status": "UP"}
