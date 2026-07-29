"""Bot handlers: start, phone linking, menu buttons, promotions, Mini App."""

from __future__ import annotations

from datetime import date

from sqlalchemy import and_, func, select
from telegram import Update
from telegram.ext import ContextTypes

from app.api.services.media_storage import media_disk_path
from app.api.services.telegram_notify import format_promotion_message
from app.config import settings
from app.database import SessionLocal
from app.models.customer import Customer
from app.models.promotion import Promotion
from app.models.reward import Reward
from bot.keyboards import (
    BTN_HELP,
    BTN_OPEN_APP,
    BTN_PROFILE,
    BTN_PROMOTIONS,
    BTN_QR,
    BTN_REWARDS,
    BTN_SHARE_PHONE,
    BTN_VISITS,
    HELP_TEXT,
    MINI_APP_HINT,
    REGISTER_FIRST_TEXT,
    WELCOME_TEXT,
    contact_request_keyboard,
    guest_menu_keyboard,
    main_menu_keyboard,
    mini_app_inline_keyboard,
)


def _normalize_phone(phone_number: str) -> str:
    phone = phone_number.replace(" ", "").replace("-", "")
    if phone.startswith("+251"):
        return "0" + phone[4:]
    if phone.startswith("251"):
        return "0" + phone[3:]
    return phone


def _find_by_telegram(telegram_id: int) -> Customer | None:
    db = SessionLocal()
    try:
        return db.scalar(select(Customer).where(Customer.telegram_id == telegram_id))
    finally:
        db.close()


def _menu_for(telegram_id: int | None):
    """Registered customers get the full grid; guests get share-phone + help."""
    if telegram_id and _find_by_telegram(telegram_id):
        return main_menu_keyboard()
    return guest_menu_keyboard()


def _link_or_create_from_contact(
    *,
    telegram_id: int,
    first_name: str,
    last_name: str | None,
    phone_number: str,
) -> tuple[Customer, bool]:
    phone = _normalize_phone(phone_number)
    db = SessionLocal()
    try:
        by_tg = db.scalar(select(Customer).where(Customer.telegram_id == telegram_id))
        if by_tg:
            if by_tg.phone_number != phone:
                conflict = db.scalar(
                    select(Customer).where(
                        Customer.phone_number == phone,
                        Customer.id != by_tg.id,
                    )
                )
                if conflict is None:
                    by_tg.phone_number = phone
                    db.commit()
                    db.refresh(by_tg)
            return by_tg, False

        by_phone = db.scalar(select(Customer).where(Customer.phone_number == phone))
        if by_phone:
            by_phone.telegram_id = telegram_id
            if first_name and not by_phone.first_name:
                by_phone.first_name = first_name
            db.commit()
            db.refresh(by_phone)
            return by_phone, False

        customer = Customer(
            telegram_id=telegram_id,
            first_name=first_name or "Guest",
            last_name=last_name,
            phone_number=phone,
        )
        db.add(customer)
        db.commit()
        db.refresh(customer)
        return customer, True
    finally:
        db.close()


def _active_promotions() -> list[Promotion]:
    db = SessionLocal()
    try:
        today = date.today()
        return list(
            db.scalars(
                select(Promotion)
                .where(
                    and_(
                        Promotion.is_active.is_(True),
                        Promotion.start_date <= today,
                        Promotion.end_date >= today,
                    )
                )
                .order_by(Promotion.start_date.desc())
            ).all()
        )
    finally:
        db.close()


def _reward_counts(customer_id) -> tuple[int, int]:
    """Returns (pending_or_active, total)."""
    db = SessionLocal()
    try:
        pending = (
            db.scalar(
                select(func.count())
                .select_from(Reward)
                .where(
                    Reward.customer_id == customer_id,
                    Reward.status == "pending",
                )
            )
            or 0
        )
        total = (
            db.scalar(
                select(func.count())
                .select_from(Reward)
                .where(Reward.customer_id == customer_id)
            )
            or 0
        )
        return pending, total
    finally:
        db.close()


async def _require_registered(update: Update) -> Customer | None:
    """If not registered, ask them to share phone and return None."""
    if not update.effective_user or not update.message:
        return None
    customer = _find_by_telegram(update.effective_user.id)
    if customer is None:
        await update.message.reply_html(
            REGISTER_FIRST_TEXT,
            reply_markup=guest_menu_keyboard(),
        )
        return None
    if not customer.is_active:
        await update.message.reply_html(
            "Your account is deactivated. Please contact the shop.",
            reply_markup=guest_menu_keyboard(),
        )
        return None
    return customer


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.effective_user or not update.message:
        return

    user = update.effective_user
    customer = _find_by_telegram(user.id)
    inline = mini_app_inline_keyboard()

    if customer is None:
        await update.message.reply_html(
            WELCOME_TEXT + "\n\nTap <b>Share phone number</b> below to register.",
            reply_markup=guest_menu_keyboard(),
        )
        if inline:
            await update.message.reply_html(
                "After registering, open the Mini App with this button:",
                reply_markup=inline,
            )
        return

    await update.message.reply_html(
        WELCOME_TEXT
        + f"\n\nWelcome back, <b>{customer.first_name}</b>!\n"
        f"Visits: <b>{customer.total_visits}</b>\n"
        "Use the menu below (or the ▦ icon next to the message box).",
        reply_markup=main_menu_keyboard(),
    )
    if inline:
        await update.message.reply_html(
            "Open the Mini App with this button:",
            reply_markup=inline,
        )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message or not update.effective_user:
        return
    await update.message.reply_html(
        HELP_TEXT,
        reply_markup=_menu_for(update.effective_user.id),
    )


async def app_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message or not update.effective_user:
        return
    keyboard = _menu_for(update.effective_user.id)
    inline = mini_app_inline_keyboard()
    if not inline:
        await update.message.reply_text(
            "Mini App URL is not configured yet. Ask the shop to set TELEGRAM_MINI_APP_URL.",
            reply_markup=keyboard,
        )
        return
    # Never send a plain https link — Telegram opens those without initData.
    await update.message.reply_html(
        "Tap the button below to open the Kings Cut Mini App.",
        reply_markup=inline,
    )


async def promos_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message or not update.effective_user:
        return

    customer = await _require_registered(update)
    if customer is None:
        return

    promos = _active_promotions()
    keyboard = main_menu_keyboard()
    if not promos:
        await update.message.reply_html(
            "No active promotions right now. Check back soon!" + MINI_APP_HINT,
            reply_markup=keyboard,
        )
        return

    await update.message.reply_html(
        f"<b>Active promotions ({len(promos)})</b>" + MINI_APP_HINT,
        reply_markup=keyboard,
    )
    for promo in promos[:5]:
        text = format_promotion_message(
            promo.title,
            promo.description,
            promo.discount_type,
            promo.discount_value,
            promo.start_date,
            promo.end_date,
        )
        media_path = media_disk_path(promo.media_filename)
        if promo.media_type == "photo" and media_path and media_path.is_file():
            with media_path.open("rb") as handle:
                await update.message.reply_photo(
                    photo=handle,
                    caption=text[:1024],
                    parse_mode="HTML",
                )
        elif promo.media_type == "video" and media_path and media_path.is_file():
            with media_path.open("rb") as handle:
                await update.message.reply_video(
                    video=handle,
                    caption=text[:1024],
                    parse_mode="HTML",
                )
        else:
            await update.message.reply_html(text)


async def profile_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message:
        return
    customer = await _require_registered(update)
    if customer is None:
        return

    last_visit = (
        customer.last_visit_date.isoformat() if customer.last_visit_date else "—"
    )
    name = f"{customer.first_name} {customer.last_name or ''}".strip()
    await update.message.reply_html(
        f"<b>Your profile</b>\n\n"
        f"Name: <b>{name}</b>\n"
        f"Phone: <b>{customer.phone_number}</b>\n"
        f"Total visits: <b>{customer.total_visits}</b>\n"
        # f"Total spending: <b>{float(customer.total_spending):,.0f} ETB</b>\n"
        f"Last visit: <b>{last_visit}</b>"
        f"{MINI_APP_HINT}",
        reply_markup=main_menu_keyboard(),
    )


async def visits_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message:
        return
    customer = await _require_registered(update)
    if customer is None:
        return

    last_visit = (
        customer.last_visit_date.isoformat() if customer.last_visit_date else "No visits yet"
    )
    await update.message.reply_html(
        f"<b>Your visits</b>\n\n"
        f"Total visits: <b>{customer.total_visits}</b>\n"
        f"Last visit: <b>{last_visit}</b>\n\n"
        "Each completed appointment or in-shop check-in adds to your visit count "
        "and loyalty progress."
        f"{MINI_APP_HINT}",
        reply_markup=main_menu_keyboard(),
    )


async def rewards_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message:
        return
    customer = await _require_registered(update)
    if customer is None:
        return

    pending, total = _reward_counts(customer.id)
    await update.message.reply_html(
        f"<b>Your rewards</b>\n\n"
        f"Ready to use: <b>{pending}</b>\n"
        f"All-time rewards: <b>{total}</b>\n\n"
        "Earn rewards by hitting visit or spending goals from our loyalty rules."
        f"{MINI_APP_HINT}",
        reply_markup=main_menu_keyboard(),
    )


async def qr_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message:
        return
    customer = await _require_registered(update)
    if customer is None:
        return

    app_line = ""
    if settings.TELEGRAM_MINI_APP_URL:
        app_line = "\n\nUse the <b>Open Kings Cut App</b> button to see your QR."

    await update.message.reply_html(
        f"<b>Your check-in QR</b>\n\n"
        f"Hi <b>{customer.first_name}</b> — show your QR at the chair so staff can "
        f"check you in.\n\n"
        f"The live QR code is inside the Mini App (Check-in tab)."
        f"{app_line}"
        f"{MINI_APP_HINT}",
        reply_markup=main_menu_keyboard(),
    )


async def contact_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message or not update.message.contact or not update.effective_user:
        return

    contact = update.message.contact
    if contact.user_id and contact.user_id != update.effective_user.id:
        await update.message.reply_text("Please share your own phone number.")
        return

    user = update.effective_user
    customer, is_new = _link_or_create_from_contact(
        telegram_id=user.id,
        first_name=contact.first_name or user.first_name or "Guest",
        last_name=contact.last_name or user.last_name,
        phone_number=contact.phone_number,
    )

    verb = "registered" if is_new else "linked"
    await update.message.reply_html(
        f"Phone {verb} ✅\n"
        f"Hi <b>{customer.first_name}</b> — you're ready to check in at the shop.\n"
        f"Visits: <b>{customer.total_visits}</b>\n\n"
        "Use the menu below (or the ▦ icon next to the message box)."
        f"{MINI_APP_HINT}",
        reply_markup=main_menu_keyboard(),
    )


async def text_menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles taps on the reply-keyboard buttons."""
    if not update.message or not update.message.text or not update.effective_user:
        return

    text = update.message.text.strip()

    if text == BTN_PROFILE:
        await profile_command(update, context)
    elif text == BTN_VISITS:
        await visits_command(update, context)
    elif text == BTN_REWARDS:
        await rewards_command(update, context)
    elif text in (BTN_PROMOTIONS, "📢 Promotions"):
        # Keep old label working if Telegram cached an older keyboard briefly.
        await promos_command(update, context)
    elif text in (BTN_HELP, "ℹ️ Help"):
        await help_command(update, context)
    elif text == BTN_QR:
        await qr_command(update, context)
    elif text == BTN_SHARE_PHONE:
        await update.message.reply_text(
            "Tap the button below to share your phone number.",
            reply_markup=contact_request_keyboard(),
        )
    elif text == BTN_OPEN_APP:
        await app_command(update, context)
