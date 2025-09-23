from typing import List, Dict
from database import pool

async def add_user(user_id: int, username: str, full_name: str):
    async with pool.acquire() as conn:
        await conn.execute(
            """
            INSERT INTO users (user_id, username, full_name)
            VALUES ($1, $2, $3)
            ON CONFLICT (user_id) DO NOTHING
            """,
            user_id, username, full_name
        )

async def get_total_users_count() -> int:
    """Возвращает общее количество пользователей."""
    async with pool.acquire() as conn:
        count = await conn.fetchval("SELECT COUNT(*) FROM users")
        return count

async def get_paginated_users(limit: int, offset: int) -> List[Dict]:
    """Возвращает список пользователей с пагинацией."""
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT u.user_id, u.username, u.full_name, COUNT(uc.course_id) AS courses_purchased
            FROM users u
            LEFT JOIN user_courses uc ON u.user_id = uc.user_id
            GROUP BY u.user_id
            ORDER BY u.registration_date DESC
            LIMIT $1 OFFSET $2
            """,
            limit, offset
        )
        return [dict(row) for row in rows]
