import aiosqlite
from config import DB_NAME
from typing import Optional, List, Dict


async def create_pending_payment(
    user_id: int, course_id: int, amount: float
) -> Optional[int]:
    # Статус платежа
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute(
            """INSERT INTO payments (user_id, course_id, amount, status)
            VALUES (?, ?, ?, 'pending')""",
            (user_id, course_id, amount),
        )
        await db.commit()
        return cursor.lastrowid


async def update_payment_status(payment_id: int, status: str):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            "UPDATE payments SET status = ? WHERE id = ?", (status, payment_id)
        )
        await db.commit()


# Отмена платежа
async def update_payment_message_id(payment_id: int, message_id: int):
    """Сохраняет ID сообщения, в котором отправлена ссылка на оплату."""
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            "UPDATE payments SET message_id = ? WHERE id = ?", (message_id, payment_id)
        )
        await db.commit()


async def get_payment_info(payment_id: int) -> Optional[Dict]:
    async with aiosqlite.connect(DB_NAME) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT user_id, course_id, message_id, status FROM payments WHERE id = ?", (payment_id,)
        )
        return await cursor.fetchone()


async def get_user_payment_history(user_id: int) -> List[Dict]:

    # История покупок пользователя

    async with aiosqlite.connect(DB_NAME) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            """
            SELECT p.amount, p.status, p.payment_date, c.title
            FROM payments p
            JOIN courses c ON p.course_id = c.id
            WHERE p.user_id = ?
            ORDER BY p.payment_date DESC
            """,
            (user_id,),
        )
        return await cursor.fetchall()


async def add_user_course(user_id: int, course_id: int):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            "INSERT OR IGNORE INTO user_courses (user_id, course_id) VALUES (?, ?)",
            (user_id, course_id),
        )
        await db.commit()
