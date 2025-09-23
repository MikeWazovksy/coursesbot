import asyncpg
import logging
from config import DB_CONFIG
import asyncio


# ------------------------------------------------------------------------------------
# Установка базы данных
async def initialize_db():
    try:
        conn = await asyncpg.connect(**DB_CONFIG)

        # Чтение SQL-скрипта
        with open("migrations/001_init.sql", "r", encoding="utf-8") as f:
            sql_script = f.read()

        # Разбиваем скрипт на отдельные команды
        # asyncpg не поддерживает executescript, поэтому выполняем по одной команде
        statements = [stmt.strip() for stmt in sql_script.split(";") if stmt.strip()]
        for stmt in statements:
            await conn.execute(stmt)

        # Проверка, есть ли колонка message_id в таблице payments
        column_exists = await conn.fetchval(
            """
            SELECT EXISTS (
                SELECT 1
                FROM information_schema.columns
                WHERE table_name='payments' AND column_name='message_id'
            )
            """
        )

        if not column_exists:
            await conn.execute("ALTER TABLE payments ADD COLUMN message_id INTEGER")

        await conn.close()
        logging.info("База данных успешно инициализирована и проверена.")

    except Exception as e:
        logging.error(f"Ошибка при инициализации БД: {e}")


