from telegram import KeyboardButton, ReplyKeyboardMarkup, Update, WebAppInfo
from telegram.ext import ContextTypes

from app.config import settings


def main_menu_keyboard() -> ReplyKeyboardMarkup:
    rows: list[list[KeyboardButton]] = []

    if settings.TELEGRAM_MINI_APP_URL:
        rows.append(
            [
                KeyboardButton(
                    text="Open Kings Cut App",
                    web_app=WebAppInfo(url=settings.TELEGRAM_MINI_APP_URL),
                )
            ]
        )

    rows.append([KeyboardButton(text="📢 Promotions"), KeyboardButton(text="ℹ️ Help")])
    rows.append([KeyboardButton(text="📱 Share phone number", request_contact=True)])

    return ReplyKeyboardMarkup(rows, resize_keyboard=True)


def contact_request_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        [[KeyboardButton(text="📱 Share phone number", request_contact=True)]],
        resize_keyboard=True,
        one_time_keyboard=True,
    )


WELCOME_TEXT = (
    "Welcome to <b>Kings Cut Addis</b> ✂️\n\n"
    "Your loyalty companion for check-ins, rewards, and shop promotions.\n\n"
    "• Open the Mini App for your personal QR code\n"
    "• View active promotions\n"
    "• Track visits and rewards\n\n"
    "Share your phone number to link your loyalty profile."
)

HELP_TEXT = (
    "<b>Commands</b>\n"
    "/start — Welcome & main menu\n"
    "/promos — Active promotions\n"
    "/app — Open Mini App link\n"
    "/help — This message\n\n"
    "Share your phone number so we can link your visits and rewards."
)
