import aiosqlite
import logging
from config import DB_NAME

async def initialize_db():
    try:
        async with aiosqlite.connect(DB_NAME) as db:
            with open("migrations/001_init.sql", "r", encoding="utf-8") as f:
                sql_script = f.read()
            await db.executescript(sql_script)
            await db.commit()
        logging.info("База данных успешно инициализирована.")
    except Exception as e:
        logging.error(f"Ошибка при инициализации БД: {e}")
