import asyncpg
from config import DB_CONFIG
from typing import List, Dict


# ------------------------------------------------------------------------------------
# Подключение к базе
async def get_connection():
    return await asyncpg.connect(**DB_CONFIG)


# ------------------------------------------------------------------------------------
# Модель курсов пользователя
async def add_user_course(user_id: int, course_id: int):
    conn = await get_connection()
    await conn.execute(
        """
        INSERT INTO user_courses (user_id, course_id)
        VALUES ($1, $2)
        ON CONFLICT (user_id, course_id) DO NOTHING
        """,
        user_id, course_id
    )
    await conn.close()


async def get_user_courses_with_details(user_id: int) -> List[Dict]:
    conn = await get_connection()
    rows = await conn.fetch(
        """
        SELECT c.title, c.materials_link
        FROM user_courses uc
        JOIN courses c ON uc.course_id = c.id
        WHERE uc.user_id = $1
        """,
        user_id
    )
    await conn.close()
    return [dict(row) for row in rows]
