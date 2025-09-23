from typing import List, Dict
from database import pool

async def add_user_course(user_id: int, course_id: int):
    async with pool.acquire() as conn:
        await conn.execute(
            """
            INSERT INTO user_courses (user_id, course_id)
            VALUES ($1, $2)
            ON CONFLICT (user_id, course_id) DO NOTHING
            """,
            user_id, course_id
        )

async def get_user_courses_with_details(user_id: int) -> List[Dict]:
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT c.title, c.materials_link
            FROM user_courses uc
            JOIN courses c ON uc.course_id = c.id
            WHERE uc.user_id = $1
            """,
            user_id
        )
        return [dict(row) for row in rows]
