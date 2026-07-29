from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    DATABASE_URL: str
    SECRET_KEY: str = "change-me-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 480  # 8 hours — workday session
    REFRESH_TOKEN_EXPIRE_DAYS: int = 14
    # Staff dashboard cookies (HttpOnly). Secure=True required in production HTTPS.
    COOKIE_SECURE: bool = False
    COOKIE_SAMESITE: str = "lax"
    TELEGRAM_BOT_TOKEN: str = ""
    TELEGRAM_MINI_APP_URL: str = ""
    # Local (or server) folder for promotion photos/videos
    UPLOAD_DIR: str = "uploads"

    @field_validator("TELEGRAM_MINI_APP_URL", mode="before")
    @classmethod
    def strip_mini_app_url(cls, value: object) -> object:
        if isinstance(value, str):
            return value.strip().rstrip("/")
        return value
    CORS_ORIGINS: list[str] = [
        "http://localhost:5173",
        "http://localhost:5174",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:5174",
    ]

    # Seed admin defaults (override in .env for production)
    ADMIN_EMAIL: str = "admin@kingscutaddis.com"
    ADMIN_PASSWORD: str = "Admin@123456"
    ADMIN_FIRST_NAME: str = "Owner"
    ADMIN_LAST_NAME: str = "Admin"
    ADMIN_PHONE: str = "0911000000"



    # Email/SMTP settings
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USERNAME: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM_EMAIL: str = "noreply@kingscutaddis.com"
    SMTP_FROM_NAME: str = "Kings Cut Addis"
    
settings = Settings()
