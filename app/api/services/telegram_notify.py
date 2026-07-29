"""Send messages via Telegram Bot API (used by admin broadcast)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Literal

import httpx

from app.config import settings

TELEGRAM_API = "https://api.telegram.org"
CAPTION_LIMIT = 1024


async def send_telegram_message(
    chat_id: int,
    text: str,
    *,
    reply_markup: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if not settings.TELEGRAM_BOT_TOKEN:
        raise RuntimeError("TELEGRAM_BOT_TOKEN is not configured")

    payload: dict[str, Any] = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": True,
    }
    if reply_markup:
        payload["reply_markup"] = reply_markup

    url = f"{TELEGRAM_API}/bot{settings.TELEGRAM_BOT_TOKEN}/sendMessage"
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(url, json=payload)
        data = response.json()
        if not data.get("ok"):
            raise RuntimeError(data.get("description", "Telegram send failed"))
        return data["result"]


async def send_telegram_media(
    chat_id: int,
    media_type: Literal["photo", "video"],
    file_path: Path,
    caption: str,
    *,
    reply_markup: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Upload a local photo/video file to Telegram (works without a public URL)."""
    if not settings.TELEGRAM_BOT_TOKEN:
        raise RuntimeError("TELEGRAM_BOT_TOKEN is not configured")
    if not file_path.is_file():
        raise RuntimeError(f"Media file not found: {file_path}")

    method = "sendPhoto" if media_type == "photo" else "sendVideo"
    field = "photo" if media_type == "photo" else "video"
    url = f"{TELEGRAM_API}/bot{settings.TELEGRAM_BOT_TOKEN}/{method}"

    form: dict[str, Any] = {
        "chat_id": str(chat_id),
        "caption": caption[:CAPTION_LIMIT],
        "parse_mode": "HTML",
    }
    if reply_markup:
        form["reply_markup"] = json.dumps(reply_markup)

    async with httpx.AsyncClient(timeout=120.0) as client:
        with file_path.open("rb") as handle:
            response = await client.post(
                url,
                data=form,
                files={field: (file_path.name, handle)},
            )
        data = response.json()
        if not data.get("ok"):
            raise RuntimeError(data.get("description", "Telegram media send failed"))
        return data["result"]


async def send_promotion_telegram(
    chat_id: int,
    message: str,
    *,
    media_type: str | None = None,
    media_path: Path | None = None,
    reply_markup: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if media_type in ("photo", "video") and media_path and media_path.is_file():
        return await send_telegram_media(
            chat_id,
            media_type,  # type: ignore[arg-type]
            media_path,
            message,
            reply_markup=reply_markup,
        )
    return await send_telegram_message(chat_id, message, reply_markup=reply_markup)


def format_promotion_message(
    title: str,
    description: str | None,
    discount_type: str | None,
    discount_value,
    start_date,
    end_date,
) -> str:
    if discount_type == "percentage":
        discount_line = f"Discount: <b>{discount_value}%</b>"
    elif discount_type == "fixed":
        discount_line = f"Discount: <b>{discount_value} ETB</b>"
    else:
        discount_line = "Special offer"

    desc = f"\n{description}" if description else ""
    return (
        f"📢 <b>{title}</b>\n"
        f"{desc}\n\n"
        f"{discount_line}\n"
        f"Valid: {start_date} → {end_date}\n\n"
        f"Open the Mini App to check in and view your loyalty rewards."
    )


def mini_app_keyboard() -> dict[str, Any] | None:
    if not settings.TELEGRAM_MINI_APP_URL:
        return None
    return {
        "inline_keyboard": [
            [{"text": "Open Kings Cut App", "web_app": {"url": settings.TELEGRAM_MINI_APP_URL}}]
        ]
    }
