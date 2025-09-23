import asyncpg
from config import DB_CONFIG
from typing import Optional, List, Dict


# ------------------------------------------------------------------------------------
# Подключение к базе
async def get_connection():
    return await asyncpg.connect(**DB_CONFIG)


# ------------------------------------------------------------------------------------
# Модель оплаты
async def create_pending_payment(user_id: int, course_id: int, amount: float) -> Optional[int]:
    conn = await get_connection()
    row = await conn.fetchrow(
        """
        INSERT INTO payments (user_id, course_id, amount, status)
        VALUES ($1, $2, $3, 'pending')
        RETURNING id
        """,
        user_id, course_id, amount
    )
    await conn.close()
    return row['id'] if row else None


async def update_payment_status(payment_id: int, status: str):
    conn = await get_connection()
    await conn.execute(
        "UPDATE payments SET status = $1 WHERE id = $2",
        status, payment_id
    )
    await conn.close()


async def update_payment_message_id(payment_id: int, message_id: int):
    conn = await get_connection()
    await conn.execute(
        "UPDATE payments SET message_id = $1 WHERE id = $2",
        message_id, payment_id
    )
    await conn.close()


async def get_payment_info(payment_id: int) -> Optional[Dict]:
    conn = await get_connection()
    row = await conn.fetchrow(
        "SELECT user_id, course_id, message_id, status FROM payments WHERE id = $1",
        payment_id
    )
    await conn.close()
    return dict(row) if row else None


async def get_user_payment_history(user_id: int) -> List[Dict]:
    conn = await get_connection()
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
    await conn.close()
    return [dict(row) for row in rows]


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
