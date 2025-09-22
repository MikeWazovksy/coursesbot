# handlers/payments.py

import logging
from aiohttp import web
from aiogram import Bot
from aiogram.utils.keyboard import InlineKeyboardBuilder
from yookassa.domain.notification import WebhookNotification

from models import payments as payments_db
from models import user_courses as user_courses_db
from keyboards.user_kb import CourseCallbackFactory

async def yookassa_webhook_handler(request: web.Request) -> web.Response:
    try:
        data = await request.json()
        bot: Bot = request.app["bot"]

        notification = WebhookNotification(data)
        payment = notification.object
        payment_id = int(payment.metadata.get("наш_внутренний_id"))

        if not payment_id:
            logging.error("В метаданных не найден ID платежа.")
            return web.Response(status=200)

        if notification.event == "payment.succeeded":
            await payments_db.update_payment_status(payment_id, "succeeded")
            payment_info = await payments_db.get_payment_info(payment_id)
            user_id = payment_info['user_id']
            course_id = payment_info['course_id']
            message_id = payment_info['message_id']

            await user_courses_db.add_user_course(user_id, course_id)

            await bot.edit_message_text(
                chat_id=user_id,
                message_id=message_id,
                text="✅ Оплата прошла успешно! Вам открыт доступ к курсу."
            )
            logging.info(f"Payment {payment_id} succeeded for user {user_id}.")

        elif notification.event == "payment.canceled":
            await payments_db.update_payment_status(payment_id, "canceled")
            payment_info = await payments_db.get_payment_info(payment_id)
            user_id = payment_info['user_id']
            course_id = payment_info['course_id']
            message_id = payment_info['message_id']

            # Создаем кнопку "Попробовать снова"
            builder = InlineKeyboardBuilder()
            builder.button(text="Попробовать снова", callback_data=CourseCallbackFactory(action="buy", course_id=course_id))

            await bot.edit_message_text(
                chat_id=user_id,
                message_id=message_id,
                text="❌ Время оплаты истекло или платёж был отменен. Ссылка больше недействительна.",
                reply_markup=builder.as_markup()
            )
            logging.info(f"Payment {payment_id} canceled for user {user_id}.")

    except Exception as e:
        logging.error(f"Ошибка при обработке вебхука от ЮKassa: {e}")

    return web.Response(status=200)
