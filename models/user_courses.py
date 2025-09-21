# models/user_courses.py

import aiosqlite
from config import DB_NAME
from typing import List, Dict


async def add_user_course(user_id: int, course_id: int):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            "INSERT OR IGNORE INTO user_courses (user_id, course_id) VALUES (?, ?)",
            (user_id, course_id),
        )
        await db.commit()


async def get_user_courses_with_details(user_id: int) -> List[Dict]:
    async with aiosqlite.connect(DB_NAME) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            """
            SELECT c.title, c.materials_link
            FROM user_courses uc
            JOIN courses c ON uc.course_id = c.id
            WHERE uc.user_id = ?
            """,
            (user_id,),
        )
        return await cursor.fetchall()
