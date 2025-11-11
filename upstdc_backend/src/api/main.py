from typing import List

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.core.config import get_settings
from src.db.mongo import register_mongo_events

settings = get_settings()

app = FastAPI(
    title=settings.APP_NAME,
    description="UPSTDC Project Monitoring System Backend APIs",
    version=settings.APP_VERSION,
    contact={"name": "UPSTDC Backend", "url": "https://upstdc.gov.in"},
    license_info={"name": "Proprietary"},
)

# Register MongoDB lifecycle hooks
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
@app.get(
    "/",
    summary="Health Check",
    tags=["Health"],
)
def health_check():
    """Simple health check endpoint.

    Returns:
        JSON object with status and database info.
    """
    db_name = settings.MONGO_DB
    # Do not perform blocking calls here; just return configured DB name.
    return {"message": "Healthy", "db": db_name}
