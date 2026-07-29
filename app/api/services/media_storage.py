"""Local filesystem helpers for promotion media uploads."""

from __future__ import annotations

import uuid
from pathlib import Path

from fastapi import HTTPException, UploadFile, status

from app.config import settings

PHOTO_TYPES = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
}
VIDEO_TYPES = {
    "video/mp4": ".mp4",
}
ALLOWED_TYPES = {**PHOTO_TYPES, **VIDEO_TYPES}

MAX_PHOTO_BYTES = 10 * 1024 * 1024
MAX_VIDEO_BYTES = 50 * 1024 * 1024


def uploads_root() -> Path:
    root = Path(settings.UPLOAD_DIR)
    if not root.is_absolute():
        root = Path.cwd() / root
    root.mkdir(parents=True, exist_ok=True)
    return root


def promotions_dir() -> Path:
    path = uploads_root() / "promotions"
    path.mkdir(parents=True, exist_ok=True)
    return path


def media_public_url(filename: str | None) -> str | None:
    if not filename:
        return None
    return f"/uploads/promotions/{filename}"


def media_disk_path(filename: str | None) -> Path | None:
    if not filename:
        return None
    return promotions_dir() / filename


def delete_media_file(filename: str | None) -> None:
    path = media_disk_path(filename)
    if path and path.is_file():
        path.unlink(missing_ok=True)


async def save_promotion_media(file: UploadFile) -> tuple[str, str]:
    """Save upload; returns (media_type, filename)."""
    content_type = (file.content_type or "").split(";")[0].strip().lower()
    if content_type not in ALLOWED_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only JPG/PNG/WebP photos or MP4 videos are allowed",
        )

    media_type = "photo" if content_type in PHOTO_TYPES else "video"
    max_bytes = MAX_PHOTO_BYTES if media_type == "photo" else MAX_VIDEO_BYTES
    data = await file.read()
    if not data:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Empty file")
    if len(data) > max_bytes:
        limit_mb = max_bytes // (1024 * 1024)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File too large (max {limit_mb} MB for {media_type})",
        )

    ext = ALLOWED_TYPES[content_type]
    filename = f"{uuid.uuid4().hex}{ext}"
    dest = promotions_dir() / filename
    dest.write_bytes(data)
    return media_type, filename
