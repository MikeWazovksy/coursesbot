import os
from dotenv import load_dotenv

load_dotenv()


# ------------------------------------------------------------------------------------
# Установка токена бота и админа(ов)
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_IDS = [
    int(admin_id) for admin_id in os.getenv("ADMIN_IDS", "").split(",") if admin_id
]


# ------------------------------------------------------------------------------------
# Telegram Payments Юкасса
PAYMENT_PROVIDER_TOKEN = os.getenv("PAYMENT_PROVIDER_TOKEN")


# ------------------------------------------------------------------------------------
# Настройки вебхука
WEBHOOK_HOST = os.getenv("WEBHOOK_HOST")


# ------------------------------------------------------------------------------------
# Настройки базы данных (PostgreSQL)
DB_CONFIG = {
    "user": os.getenv("DB_USER", "postgres"),
    "password": os.getenv("DB_PASSWORD", ""),
    "database": os.getenv("DB_NAME", "postgres"),
    "host": os.getenv("DB_HOST", "localhost"),
    "port": int(os.getenv("DB_PORT", 5432))
}
