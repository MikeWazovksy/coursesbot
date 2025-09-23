import os
from dotenv import load_dotenv

load_dotenv()

# --- Основные настройки ---
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_IDS = [
    int(admin_id) for admin_id in os.getenv("ADMIN_IDS", "").split(",") if admin_id
]

# --- Встроенные платежи Telegram ---
PAYMENT_PROVIDER_TOKEN = os.getenv("PAYMENT_PROVIDER_TOKEN")

# --- Настройки вебхука ---
WEBHOOK_HOST = os.getenv("WEBHOOK_HOST")

# --- Настройки базы данных (PostgreSQL) ---
DATABASE_URL = os.getenv("DATABASE_URL")
