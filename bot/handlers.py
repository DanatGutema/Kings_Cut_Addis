"""Bot handlers: start, phone linking, promotions, Mini App."""

from __future__ import annotations

from datetime import date

from sqlalchemy import and_, select
from telegram import Update
from telegram.ext import ContextTypes

from app.api.services.telegram_notify import format_promotion_message
from app.config import settings
from app.database import SessionLocal
from app.models.customer import Customer
from app.models.promotion import Promotion
from bot.keyboards import (
    HELP_TEXT,
    WELCOME_TEXT,
    contact_request_keyboard,
    main_menu_keyboard,
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


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.effective_user or not update.message:
        return

    user = update.effective_user
    customer = _find_by_telegram(user.id)

    if customer is None:
        await update.message.reply_html(
            WELCOME_TEXT + "\n\nTap below to share your phone and activate loyalty.",
            reply_markup=contact_request_keyboard(),
        )
        return

    await update.message.reply_html(
        WELCOME_TEXT
        + f"\n\nWelcome back, <b>{customer.first_name}</b>!\n"
        f"Loyalty: <b>{customer.loyalty_status}</b> · Visits: <b>{customer.total_visits}</b>",
        reply_markup=main_menu_keyboard(),
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message:
        return
    await update.message.reply_html(HELP_TEXT, reply_markup=main_menu_keyboard())


async def app_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message:
        return
    if not settings.TELEGRAM_MINI_APP_URL:
        await update.message.reply_text(
            "Mini App URL is not configured yet. Ask the shop to set TELEGRAM_MINI_APP_URL."
        )
        return
    await update.message.reply_html(
        f'Open the app: <a href="{settings.TELEGRAM_MINI_APP_URL}">Kings Cut Mini App</a>',
        reply_markup=main_menu_keyboard(),
    )


async def promos_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message:
        return

    promos = _active_promotions()
    if not promos:
        await update.message.reply_html(
            "No active promotions right now. Check back soon!",
            reply_markup=main_menu_keyboard(),
        )
        return

    await update.message.reply_html(
        f"<b>Active promotions ({len(promos)})</b>",
        reply_markup=main_menu_keyboard(),
    )
    for promo in promos:
        text = format_promotion_message(
            promo.title,
            promo.description,
            promo.discount_type,
            promo.discount_value,
            promo.start_date,
            promo.end_date,
        )
        await update.message.reply_html(text)


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
        f"Loyalty: <b>{customer.loyalty_status}</b> · Visits: <b>{customer.total_visits}</b>",
        reply_markup=main_menu_keyboard(),
    )


async def text_menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message or not update.message.text:
        return

    text = update.message.text.strip()
    if text == "📢 Promotions":
        await promos_command(update, context)
    elif text == "ℹ️ Help":
        await help_command(update, context)
    elif text == "📱 Share phone number":
        await update.message.reply_text(
            "Tap the button below to share your phone number.",
            reply_markup=contact_request_keyboard(),
        )
