import asyncpg
from config import DB_CONFIG
from typing import Dict


# ------------------------------------------------------------------------------------
# Подключение к базе
async def get_connection():
    return await asyncpg.connect(**DB_CONFIG)


# ------------------------------------------------------------------------------------
# Модель статистики
async def get_main_stats() -> Dict:
    conn = await get_connection()

    # Кол-во пользователей
    users_count = await conn.fetchval("SELECT COUNT(*) FROM users")

    # Кол-во покупок
    purchases_count = await conn.fetchval("SELECT COUNT(*) FROM user_courses")

    # Кол-во успешных платежей и общая выручка
    payments_row = await conn.fetchrow(
        "SELECT COUNT(*) AS count, SUM(amount) AS total FROM payments WHERE status = 'succeeded'"
    )
    successful_payments_count = payments_row['count'] or 0
    total_revenue = float(payments_row['total'] or 0.0)

    # Кол-во активных курсов
    active_courses_count = await conn.fetchval("SELECT COUNT(*) FROM courses")

    await conn.close()

    return {
        "users_count": users_count,
        "purchases_count": purchases_count,
        "successful_payments_count": successful_payments_count,
        "total_revenue": total_revenue,
        "active_courses_count": active_courses_count,
    }
