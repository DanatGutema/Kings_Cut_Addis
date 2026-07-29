from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.services.media_storage import uploads_root
from app.api.v1.router import api_router
from app.config import settings

app = FastAPI(
    title="Kings Cut Addis API",
    description="Loyalty & management system for barber shop",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api/v1")

# Serve uploaded promotion media (dev: ./uploads, prod: same path on server)
_uploads = uploads_root()
_uploads.mkdir(parents=True, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=str(_uploads)), name="uploads")


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}
