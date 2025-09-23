import asyncpg
from config import DB_CONFIG  # словарь с host, user, password, database, port
from typing import List, Tuple, Optional


# ------------------------------------------------------------------------------------
# Подключение к базе
async def get_connection():
    return await asyncpg.connect(**DB_CONFIG)


# ------------------------------------------------------------------------------------
# Модель курсов
async def get_all_courses() -> List[asyncpg.Record]:
    conn = await get_connection()
    rows = await conn.fetch("SELECT * FROM courses")
    await conn.close()
    return rows


async def get_course_by_id(course_id: int) -> Optional[asyncpg.Record]:
    conn = await get_connection()
    row = await conn.fetchrow("SELECT * FROM courses WHERE id = $1", course_id)
    await conn.close()
    return row


async def add_course(
    title: str, short_desc: str, full_desc: str, link: str, price: float
):
    conn = await get_connection()
    await conn.execute(
        """
        INSERT INTO courses (title, short_description, full_description, materials_link, price)
        VALUES ($1, $2, $3, $4, $5)
        """,
        title, short_desc, full_desc, link, price
    )
    await conn.close()


async def delete_course(course_id: int):
    conn = await get_connection()
    await conn.execute("DELETE FROM courses WHERE id = $1", course_id)
    await conn.close()


async def update_course_field(course_id: int, field: str, value):
    # В PostgreSQL параметры запроса не могут подставлять имена полей,
    # поэтому делаем динамический SQL безопасно
    if field not in {"title", "short_description", "full_description", "materials_link", "price"}:
        raise ValueError("Недопустимое поле")
    conn = await get_connection()
    await conn.execute(f"UPDATE courses SET {field} = $1 WHERE id = $2", value, course_id)
    await conn.close()
