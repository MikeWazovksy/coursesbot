import aiosqlite
from config import DB_NAME
from typing import List, Tuple, Optional


async def get_all_courses() -> List[Tuple]:
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute("SELECT * FROM courses")
        return await cursor.fetchall()


async def get_course_by_id(course_id: int) -> Optional[Tuple]:
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute("SELECT * FROM courses WHERE id = ?", (course_id,))
        return await cursor.fetchone()


async def add_course(title: str, short_desc: str, full_desc: str, link: str, price: float):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            """INSERT INTO courses (title, short_description, full_description, materials_link, price)
            VALUES (?, ?, ?, ?, ?)""",
            (title, short_desc, full_desc, link, price)
        )
        await db.commit()


async def delete_course(course_id: int):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("DELETE FROM courses WHERE id = ?", (course_id,))
        await db.commit()


async def update_course_field(course_id: int, field: str, value):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            f"UPDATE courses SET {field} = ? WHERE id = ?", (value, course_id)
        )
        await db.commit()
