from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from src.api.deps.db import require_db_available

router = APIRouter(prefix="/projects", tags=["Projects"])

# PUBLIC_INTERFACE
@router.get(
    "",
    summary="List projects",
    description="Example endpoint requiring DB. Returns 503 if DB is unavailable.",
    responses={
        200: {"description": "Projects listed"},
        503: {"description": "Database unavailable"},
    },
)
async def list_projects(db=Depends(require_db_available)) -> dict:
    """List projects (example). Uses DB dependency to enforce availability."""
    try:
        # Example no-op to show usage; real implementation would query the DB.
        # Avoid leaking any DB info.
        _ = db.name  # touch to avoid linter flags
        return {"items": [], "total": 0}
    except HTTPException:
        # bubble up 503 raised by dependency
        raise
    except Exception:
        # Generic safe error handling
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unexpected server error",
        )
