import aiosqlite
from config import DB_NAME
from typing import List, Dict


async def add_user(user_id: int, username: str, full_name: str):

    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            "INSERT OR IGNORE INTO users (user_id, username, full_name) VALUES (?, ?, ?)",
            (user_id, username, full_name),
        )
        await db.commit()


async def get_total_users_count() -> int:
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute("SELECT COUNT(*) FROM users")
        return (await cursor.fetchone())[0]


async def get_paginated_users(limit: int, offset: int) -> List[Dict]:

    async with aiosqlite.connect(DB_NAME) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            """
            SELECT u.user_id, u.username, u.full_name, COUNT(uc.course_id) as courses_purchased
            FROM users u
            LEFT JOIN user_courses uc ON u.user_id = uc.user_id
            GROUP BY u.user_id
            ORDER BY u.registration_date DESC
            LIMIT ? OFFSET ?
            """,
            (limit, offset),
        )
        return await cursor.fetchall()
