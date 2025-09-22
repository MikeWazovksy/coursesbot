# handlers/payments.py

import logging
import asyncio
from aiohttp import web
from aiogram import Bot
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.exceptions import TelegramBadRequest
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
        metadata = payment.metadata

        payment_id = int(metadata.get("payment_id"))
        user_id = int(metadata.get("user_id"))
        course_id = int(metadata.get("course_id"))
        message_id = int(metadata.get("message_id"))

        if not all([payment_id, user_id, course_id, message_id]):
            logging.error(f"Недостаточно метаданных в вебхуке от ЮKassa: {metadata}")
            return web.Response(status=200)

        # --- ОСНОВНАЯ ЛОГИКА ---
        if notification.event == "payment.succeeded":
            await payments_db.update_payment_status(payment_id, "succeeded")
            await user_courses_db.add_user_course(user_id, course_id)

            await bot.edit_message_text(
                chat_id=user_id, message_id=message_id,
                text="✅ Оплата прошла успешно! Вам открыт доступ к курсу."
            )
            logging.info(f"Payment {payment_id} succeeded for user {user_id}.")

        elif notification.event == "payment.canceled":
            # --- ДИАГНОСТИЧЕСКОЕ ЛОГИРОВАНИЕ ---
            logging.warning(f"--- НАЧАТА ОБРАБОТКА ОТМЕНЫ ПЛАТЕЖА ID: {payment_id} ---")
            logging.warning(f"Данные из metadata: user_id={user_id}, message_id={message_id}, course_id={course_id}")

            await payments_db.update_payment_status(payment_id, "canceled")
            logging.warning("Статус в БД успешно изменен на 'canceled'.")

            builder = InlineKeyboardBuilder()
            builder.button(text="Попробовать снова", callback_data=CourseCallbackFactory(action="buy", course_id=course_id))

            text_to_send = "❌ Время оплаты истекло или платёж был отменен. Ссылка больше недействительна."

            try:
                logging.warning(f"Пытаюсь отредактировать сообщение: chat_id={user_id}, message_id={message_id}")
                await bot.edit_message_text(
                    chat_id=user_id,
                    message_id=message_id,
                    text=text_to_send,
                    reply_markup=builder.as_markup()
                )
                logging.warning("--- УСПЕШНОЕ ЗАВЕРШЕНИЕ bot.edit_message_text ---")
            except Exception as e:
                logging.error(f"!!! ОШИБКА ПРИ ВЫЗОВЕ bot.edit_message_text: {e}", exc_info=True)

            logging.info(f"Payment {payment_id} canceled for user {user_id}.")

    except Exception as e:
        logging.error(f"Критическая ошибка при обработке вебхука от ЮKassa: {e}", exc_info=True)

    return web.Response(status=200)
