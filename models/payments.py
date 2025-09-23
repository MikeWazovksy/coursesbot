from typing import Optional, List, Dict
import asyncpg

async def create_pending_payment(pool: asyncpg.Pool, user_id: int, course_id: int, amount: float) -> Optional[int]:
    async with pool.acquire() as conn:
        payment_id = await conn.fetchval(
            """
            INSERT INTO payments (user_id, course_id, amount, status)
            VALUES ($1, $2, $3, 'pending')
            RETURNING id
            """,
            user_id, course_id, amount
        )
        return payment_id

async def update_payment_status(pool: asyncpg.Pool, payment_id: int, status: str):
    async with pool.acquire() as conn:
        await conn.execute(
            "UPDATE payments SET status = $1 WHERE id = $2",
            status, payment_id
        )

async def update_payment_message_id(pool: asyncpg.Pool, payment_id: int, message_id: int):
    async with pool.acquire() as conn:
        await conn.execute(
            "UPDATE payments SET message_id = $1 WHERE id = $2",
            message_id, payment_id
        )

async def get_payment_info(pool: asyncpg.Pool, payment_id: int) -> Optional[Dict]:
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT user_id, course_id, message_id, status FROM payments WHERE id = $1",
            payment_id
        )
        return dict(row) if row else None

async def get_user_payment_history(pool: asyncpg.Pool, user_id: int) -> List[Dict]:
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT p.amount, p.status, p.payment_date, c.title
            FROM payments p
            JOIN courses c ON p.course_id = c.id
            WHERE p.user_id = $1
            ORDER BY p.payment_date DESC
            """,
            user_id
        )
        return [dict(row) for row in rows]
