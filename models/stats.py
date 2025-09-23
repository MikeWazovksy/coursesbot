from typing import Dict
import asyncpg

async def get_main_stats(pool: asyncpg.Pool) -> Dict:
    async with pool.acquire() as conn:
        query = """
        SELECT
            (SELECT COUNT(*) FROM users) AS users_count,
            (SELECT COUNT(*) FROM user_courses) AS purchases_count,
            (SELECT COUNT(*) FROM payments WHERE status = 'succeeded') AS successful_payments_count,
            (SELECT SUM(amount) FROM payments WHERE status = 'succeeded') AS total_revenue,
            (SELECT COUNT(*) FROM courses) AS active_courses_count
        """
        stats_row = await conn.fetchrow(query)

    return {
        "users_count": stats_row['users_count'] or 0,
        "purchases_count": stats_row['purchases_count'] or 0,
        "successful_payments_count": stats_row['successful_payments_count'] or 0,
        "total_revenue": float(stats_row['total_revenue'] or 0.0),
        "active_courses_count": stats_row['active_courses_count'] or 0,
    }
