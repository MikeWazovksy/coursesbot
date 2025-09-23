import aiosqlite
import logging
from config import DB_NAME


# ------------------------------------------------------------------------------------
# Установка базы данных
async def initialize_db():
    try:
        async with aiosqlite.connect(DB_NAME) as db:
            with open("migrations/001_init.sql", "r", encoding="utf-8") as f:
                sql_script = f.read()
            await db.executescript(sql_script)

            cursor = await db.execute("PRAGMA table_info(payments)")
            columns = [row[1] for row in await cursor.fetchall()]

            if "message_id" not in columns:
                await db.execute("ALTER TABLE payments ADD COLUMN message_id INTEGER")

            await db.commit()
            logging.info("База данных успешно инициализирована и проверена.")

    except Exception as e:
        logging.error(f"Ошибка при инициализации БД: {e}")
