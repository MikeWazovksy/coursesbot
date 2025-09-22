# handlers/payments.py

import logging
import asyncio
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
            logging.error("В метаданных ЮKassa не найден наш внутренний ID платежа.")
            return web.Response(status=200)

        payment_info = await payments_db.get_payment_info(payment_id)

        # ИСПРАВЛЕНИЕ ЗДЕСЬ: используем [] вместо .get()
        if payment_info and not payment_info['message_id']:
            logging.warning(f"Message_id для платежа {payment_id} еще не записан. Ждем 2 секунды и пробуем снова.")
            await asyncio.sleep(2)
            payment_info = await payments_db.get_payment_info(payment_id)

        if not payment_info:
            logging.error(f"Платёж с ID {payment_id} не найден в нашей базе данных после ожидания.")
            return web.Response(status=200)

        # ИСПРАВЛЕНИЕ ЗДЕСЬ: используем [] вместо .get()
        user_id = payment_info['user_id']
        course_id = payment_info['course_id']
        message_id = payment_info['message_id']

        if not all([user_id, course_id, message_id]):
            logging.error(f"Недостаточно данных для платежа ID {payment_id}. user_id: {user_id}, course_id: {course_id}, message_id: {message_id}")
            return web.Response(status=200)

        if notification.event == "payment.succeeded":
            await payments_db.update_payment_status(payment_id, "succeeded")
            await user_courses_db.add_user_course(user_id, course_id)

            await bot.edit_message_text(
                chat_id=user_id,
                message_id=message_id,
                text="✅ Оплата прошла успешно! Вам открыт доступ к курсу."
            )
            logging.info(f"Payment {payment_id} succeeded for user {user_id}.")

        elif notification.event == "payment.canceled":
            await payments_db.update_payment_status(payment_id, "canceled")

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
        logging.error(f"Критическая ошибка при обработке вебхука от ЮKassa: {e}", exc_info=True)

    return web.Response(status=200)
