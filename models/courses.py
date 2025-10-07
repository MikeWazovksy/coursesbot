from typing import List, Optional
import asyncpg


async def get_all_courses(pool: asyncpg.Pool) -> List:
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            "SELECT * FROM courses WHERE is_active = TRUE ORDER BY id"
        )
        return rows


async def get_course_by_id(pool: asyncpg.Pool, course_id: int) -> Optional:
    async with pool.acquire() as conn:
        row = await conn.fetchrow("SELECT * FROM courses WHERE id = $1", course_id)
        return row


async def add_course(
    pool: asyncpg.Pool,
    title: str,
    short_desc: str,
    full_desc: str,
    link: str,
    price: float,
):
    async with pool.acquire() as conn:
        await conn.execute(
            """
            INSERT INTO courses (title, short_description, full_description, materials_link, price)
            VALUES ($1, $2, $3, $4, $5)
            """,
            title,
            short_desc,
            full_desc,
            link,
            price,
        )


async def delete_course(pool: asyncpg.Pool, course_id: int):
    async with pool.acquire() as conn:
        await conn.execute(
            "UPDATE courses SET is_active = FALSE WHERE id = $1", course_id
        )


async def update_course_field(pool: asyncpg.Pool, course_id: int, field: str, value):
    if field not in {
        "title",
        "short_description",
        "full_description",
        "materials_link",
        "price",
        "is_active",
    }:
        raise ValueError("Недопустимое поле для обновления")

    async with pool.acquire() as conn:
        await conn.execute(
            f"UPDATE courses SET {field} = $1 WHERE id = $2", value, course_id
        )


async def get_total_courses_count(pool: asyncpg.Pool) -> int:
    async with pool.acquire() as conn:
        count = await conn.fetchval(
            "SELECT COUNT(*) FROM courses WHERE is_active = TRUE"
        )
        return count


async def get_paginated_courses(pool: asyncpg.Pool, limit: int, offset: int) -> List:
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT *
            FROM courses
            WHERE is_active = TRUE
            ORDER BY id
            LIMIT $1 OFFSET $2
            """,
            limit,
            offset,
        )
        return rows


async def get_total_archived_courses_count(pool: asyncpg.Pool) -> int:
    async with pool.acquire() as conn:
        count = await conn.fetchval(
            "SELECT COUNT(*) FROM courses WHERE is_active = FALSE"
        )
        return count


async def get_paginated_archived_courses(
    pool: asyncpg.Pool, limit: int, offset: int
) -> List:
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT *
            FROM courses
            WHERE is_active = FALSE
            ORDER BY id
            LIMIT $1 OFFSET $2
            """,
            limit,
            offset,
        )
        return rows
