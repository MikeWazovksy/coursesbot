# handlers/payments.py

import logging
from aiohttp import web
from aiogram import Bot
from yookassa.domain.notification import WebhookNotification
from models import payments as payments_db
from models import user_courses as user_courses_db


async def yookassa_webhook_handler(request: web.Request) -> web.Response:
    try:
        data = await request.json()
        bot: Bot = request.app["bot"]

        notification = WebhookNotification(data)
        payment = notification.object

        if notification.event == "payment.succeeded" and payment.status == "succeeded":
            payment_id = int(payment.metadata.get("наш_внутренний_id"))

            await payments_db.update_payment_status(payment_id, "succeeded")

            payment_info = await payments_db.get_payment_info(payment_id)
            user_id = payment_info["user_id"]
            course_id = payment_info["course_id"]

            await user_courses_db.add_user_course(user_id, course_id)

            await bot.send_message(
                chat_id=user_id,
                text="✅ Оплата прошла успешно! Вам открыт доступ к курсу. Вы можете найти его в разделе '📚 Мои курсы'.",
            )
            logging.info(f"Payment {payment_id} for user {user_id} succeeded.")

    except Exception as e:
        logging.error(f"Error processing YooKassa webhook: {e}")

    return web.Response(status=200)
