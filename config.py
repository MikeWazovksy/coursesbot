import os
from dotenv import load_dotenv

load_dotenv()

# Основные настройки
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_IDS = [
    int(admin_id) for admin_id in os.getenv("ADMIN_IDS", "").split(",") if admin_id
]

# Настройки ЮKassa

YOOKASSA_SHOP_ID = os.getenv("YOOKASSA_SHOP_ID")
YOOKASSA_SECRET_KEY = os.getenv("YOOKASSA_SECRET_KEY")

# Настройки вебхука
WEBHOOK_HOST = os.getenv("WEBHOOK_HOST")

# Настройки базы данных
DB_NAME = "database.db"
