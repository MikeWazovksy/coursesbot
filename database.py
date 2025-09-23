import asyncpg
import logging
from config import DB_CONFIG

pool = None

async def create_pool():
    global pool
    if pool is None:
        try:
            pool = await asyncpg.create_pool(**DB_CONFIG)
            logging.info("Пул соединений с PostgreSQL успешно создан.")
        except Exception as e:
            logging.error(f"Не удалось создать пул соединений: {e}", exc_info=True)

async def initialize_db():
    if not pool:
        logging.error("Пул соединений не был создан. Инициализация БД невозможна.")
        return

    async with pool.acquire() as conn:
        try:
            with open("migrations/001_init.sql", "r", encoding="utf-8") as f:
                sql_script = f.read()

            statements = [stmt.strip() for stmt in sql_script.split(";") if stmt.strip()]
            for stmt in statements:
                await conn.execute(stmt)

            logging.info("Основные таблицы успешно созданы (или уже существовали).")

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
                logging.warning("Обнаружена старая структура БД. Добавляем колонку 'message_id'...")
                await conn.execute("ALTER TABLE payments ADD COLUMN message_id BIGINT")
                logging.info("Колонка 'message_id' успешно добавлена.")

            logging.info("База данных успешно инициализирована и проверена.")

        except Exception as e:
            logging.error(f"Ошибка при инициализации БД: {e}", exc_info=True)
