"""Telegram reply keyboards and static bot copy."""

from __future__ import annotations

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup, WebAppInfo

from app.config import settings

# Exact button labels — handlers match these strings.
BTN_PROFILE = "📋 Profile"
BTN_REWARDS = "🎁 Rewards"
BTN_VISITS = "📊 Visits"
BTN_PROMOTIONS = "🏷️ Promotions"
BTN_HELP = "❓ Help"
BTN_QR = "📱 QR Code"
BTN_SHARE_PHONE = "📱 Share phone number"
BTN_OPEN_APP = "Open Kings Cut App"

MINI_APP_HINT = (
    "\n\n📲 <i>For more details, open the <b>Kings Cut Mini App</b>.</i>"
)

REGISTER_FIRST_TEXT = (
    "Please <b>register first</b> by sharing your phone number.\n\n"
    "That links your Telegram to your loyalty profile so we can show "
    "visits, rewards, and your check-in QR."
)


def _open_app_row() -> list[KeyboardButton]:
    if not settings.TELEGRAM_MINI_APP_URL:
        return []
    return [
        KeyboardButton(
            text=BTN_OPEN_APP,
            web_app=WebAppInfo(url=settings.TELEGRAM_MINI_APP_URL),
        )
    ]


def mini_app_inline_keyboard() -> InlineKeyboardMarkup | None:
    """Inline WebApp button — more reliable than HTML links for initData."""
    if not settings.TELEGRAM_MINI_APP_URL:
        return None
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    text="Open Kings Cut App",
                    web_app=WebAppInfo(url=settings.TELEGRAM_MINI_APP_URL),
                )
            ]
        ]
    )


def guest_menu_keyboard() -> ReplyKeyboardMarkup:
    """Shown before phone registration. Share-phone is always available."""
    rows: list[list[KeyboardButton]] = []
    # app_row = _open_app_row()
    # if app_row:
    #     rows.append(app_row)
    rows.append([KeyboardButton(text=BTN_SHARE_PHONE, request_contact=True)])
    rows.append([KeyboardButton(text=BTN_HELP)])
    return ReplyKeyboardMarkup(rows, resize_keyboard=True)


def main_menu_keyboard() -> ReplyKeyboardMarkup:
    """Full menu for registered customers (4-dot panel near the message box)."""
    rows: list[list[KeyboardButton]] = []
    # app_row = _open_app_row()
    # if app_row:
    #     rows.append(app_row)

    rows.append([KeyboardButton(text=BTN_PROFILE), KeyboardButton(text=BTN_REWARDS)])
    rows.append([KeyboardButton(text=BTN_VISITS), KeyboardButton(text=BTN_PROMOTIONS)])
    rows.append([KeyboardButton(text=BTN_HELP), KeyboardButton(text=BTN_QR)])
    # Always keep share-phone so they can re-link / update phone.
    rows.append([KeyboardButton(text=BTN_SHARE_PHONE, request_contact=True)])

    return ReplyKeyboardMarkup(rows, resize_keyboard=True)


def contact_request_keyboard() -> ReplyKeyboardMarkup:
    """One-time focused prompt to share contact."""
    return ReplyKeyboardMarkup(
        [[KeyboardButton(text=BTN_SHARE_PHONE, request_contact=True)]],
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
    "<b>How Kings Cut works</b>\n\n"
    "• <b>Share phone</b> — register / link your loyalty account\n"
    "• <b>Profile / Visits / Rewards</b> — quick summaries here in chat\n"
    "• <b>QR Code</b> — check in at the shop (full QR is in the Mini App)\n"
    "• <b>Promotions</b> — current shop offers\n\n"
    "• <b>Wanna Contact The Staff? 0974963344</b>\n\n"
    "<b>Commands</b>\n"
    "/start — Welcome & menu\n"
    "/promos — Active promotions\n"
    "/app — Mini App link\n"
    "/help — This message\n"
    f"{MINI_APP_HINT}"
)
