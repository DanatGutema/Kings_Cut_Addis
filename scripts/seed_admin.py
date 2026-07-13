"""Create the initial admin staff account."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from sqlalchemy import select

from app.api.core.security import hash_password
from app.config import settings
from app.database import SessionLocal
from app.models.staff import Staff


def main() -> int:
    db = SessionLocal()
    try:
        existing = db.scalar(select(Staff).where(Staff.email == settings.ADMIN_EMAIL))
        if existing:
            print(f"Admin already exists: {settings.ADMIN_EMAIL}")
            return 0

        admin = Staff(
            first_name=settings.ADMIN_FIRST_NAME,
            last_name=settings.ADMIN_LAST_NAME,
            phone_number=settings.ADMIN_PHONE,
            email=settings.ADMIN_EMAIL,
            password_hash=hash_password(settings.ADMIN_PASSWORD),
            role="admin",
            is_active=True,
        )
        db.add(admin)
        db.commit()
        db.refresh(admin)

        print("Admin user created successfully.")
        print(f"  Email:    {settings.ADMIN_EMAIL}")
        print(f"  Password: {settings.ADMIN_PASSWORD}")
        print(f"  Role:     admin")
        print(f"  ID:       {admin.id}")
        print("\nChange the password after first login.")
        return 0
    finally:
        db.close()


if __name__ == "__main__":
    raise SystemExit(main())
