import aiosqlite
import logging
from config import DB_NAME

async def initialize_db():
    try:
        async with aiosqlite.connect(DB_NAME) as db:
            # 1. Создаем основные таблицы, если их нет
            with open("migrations/001_init.sql", "r", encoding="utf-8") as f:
                sql_script = f.read()
            await db.executescript(sql_script)

            # 2. Проверяем наличие колонки message_id в таблице payments
            cursor = await db.execute("PRAGMA table_info(payments)")
            columns = [row[1] for row in await cursor.fetchall()]

            # 3. Если колонки нет - добавляем ее
            if 'message_id' not in columns:
                logging.warning("Обнаружена старая структура БД. Добавляем колонку 'message_id'...")
                await db.execute("ALTER TABLE payments ADD COLUMN message_id INTEGER")
                logging.info("Колонка 'message_id' успешно добавлена.")

            await db.commit()
            logging.info("База данных успешно инициализирована и проверена.")

    except Exception as e:
        logging.error(f"Ошибка при инициализации БД: {e}")
