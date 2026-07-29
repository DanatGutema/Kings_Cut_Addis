"""Telegram bot entrypoint for Kings Cut Addis.

Run:
  python -m bot.main

Requires TELEGRAM_BOT_TOKEN in .env
Optional: TELEGRAM_MINI_APP_URL for the Mini App button
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path

# Ensure project root is on sys.path when run as script
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from telegram import MenuButtonWebApp, WebAppInfo
from telegram.ext import Application, CommandHandler, MessageHandler, filters

from app.config import settings
from bot.handlers import (
    app_command,
    contact_handler,
    help_command,
    profile_command,
    promos_command,
    qr_command,
    rewards_command,
    start_command,
    text_menu_handler,
    visits_command,
)

logging.basicConfig(
    format="%(asctime)s | %(name)s | %(levelname)s | %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger("kingscut.bot")


async def _set_menu_button(application: Application) -> None:
    """Force BotFather-style menu button to WebApp mode (not a plain URL)."""
    url = (settings.TELEGRAM_MINI_APP_URL or "").strip()
    if not url:
        return
    await application.bot.set_chat_menu_button(
        menu_button=MenuButtonWebApp(
            text="Open App",
            web_app=WebAppInfo(url=url),
        )
    )
    logger.info("Chat menu button set to WebApp: %s", url)


def build_app() -> Application:
    if not settings.TELEGRAM_BOT_TOKEN:
        raise SystemExit(
            "TELEGRAM_BOT_TOKEN is missing. Create a bot with @BotFather and add the token to .env"
        )

    application = (
        Application.builder()
        .token(settings.TELEGRAM_BOT_TOKEN)
        .post_init(_set_menu_button)
        .read_timeout(30)
        .write_timeout(30)
        .connect_timeout(30)
        .build()
    )

    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("promos", promos_command))
    application.add_handler(CommandHandler("promotions", promos_command))
    application.add_handler(CommandHandler("profile", profile_command))
    application.add_handler(CommandHandler("visits", visits_command))
    application.add_handler(CommandHandler("rewards", rewards_command))
    application.add_handler(CommandHandler("qr", qr_command))
    application.add_handler(CommandHandler("app", app_command))
    application.add_handler(MessageHandler(filters.CONTACT, contact_handler))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_menu_handler))

    return application


def main() -> None:
    app = build_app()
    logger.info("Kings Cut bot starting (polling)...")
    if settings.TELEGRAM_MINI_APP_URL:
        logger.info("Mini App URL: %s", settings.TELEGRAM_MINI_APP_URL)
    else:
        logger.warning("TELEGRAM_MINI_APP_URL not set — Mini App button disabled")
    app.run_polling(allowed_updates=["message"])


if __name__ == "__main__":
    main()
