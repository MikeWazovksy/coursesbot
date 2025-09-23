import asyncpg
from config import DB_CONFIG
from typing import List, Dict


# ------------------------------------------------------------------------------------
# Подключение к базе
async def get_connection():
    return await asyncpg.connect(**DB_CONFIG)


# ------------------------------------------------------------------------------------
# Модель пользователей
async def add_user(user_id: int, username: str, full_name: str):
    conn = await get_connection()
    await conn.execute(
        """
        INSERT INTO users (user_id, username, full_name)
        VALUES ($1, $2, $3)
        ON CONFLICT (user_id) DO NOTHING
        """,
        user_id, username, full_name
    )
    await conn.close()


async def get_total_users_count() -> int:
    conn = await get_connection()
    count = await conn.fetchval("SELECT COUNT(*) FROM users")
    await conn.close()
    return count


async def get_paginated_users(limit: int, offset: int) -> List[Dict]:
    conn = await get_connection()
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
    await conn.close()
    return [dict(row) for row in rows]
