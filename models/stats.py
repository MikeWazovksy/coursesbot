# models/stats.py
import aiosqlite
from config import DB_NAME
from typing import Dict


async def get_main_stats() -> Dict:
    """Собирает основную статистику из базы данных."""
    async with aiosqlite.connect(DB_NAME) as db:
        # Количество пользователей
        users_cursor = await db.execute("SELECT COUNT(*) FROM users")
        users_count = (await users_cursor.fetchone())[0]

        # Количество купленных курсов
        purchases_cursor = await db.execute("SELECT COUNT(*) FROM user_courses")
        purchases_count = (await purchases_cursor.fetchone())[0]

        # Статистика по платежам
        payments_cursor = await db.execute(
            "SELECT COUNT(*), SUM(amount) FROM payments WHERE status = 'succeeded'"
        )
        payments_data = await payments_cursor.fetchone()
        successful_payments_count = payments_data[0] or 0
        total_revenue = payments_data[1] or 0.0

        # Количество активных курсов
        courses_cursor = await db.execute("SELECT COUNT(*) FROM courses")
        active_courses_count = (await courses_cursor.fetchone())[0]

        return {
            "users_count": users_count,
            "purchases_count": purchases_count,
            "successful_payments_count": successful_payments_count,
            "total_revenue": total_revenue,
            "active_courses_count": active_courses_count,
        }
