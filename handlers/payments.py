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

        # --- ШАГ 1: ИЗВЛЕКАЕМ ВСЕ ДАННЫЕ ИЗ METADATA ---
        metadata = payment.metadata
        payment_id = int(metadata.get("payment_id"))
        user_id = int(metadata.get("user_id"))
        course_id = int(metadata.get("course_id"))
        message_id = int(metadata.get("message_id"))

        if not all([payment_id, user_id, course_id, message_id]):
            logging.error(f"Недостаточно метаданных в вебхуке от ЮKassa: {metadata}")
            return web.Response(status=200)

        # --- ШАГ 2: ПРОВЕРЯЕМ СТАТУС В НАШЕЙ БД (чтобы избежать повторной обработки) ---
        payment_info = await payments_db.get_payment_info(payment_id)
        if payment_info and payment_info['status'] != 'pending':
            logging.info(f"Повторный вебхук для уже обработанного платежа {payment_id}. Игнорируем.")
            return web.Response(status=200)

        # --- ШАГ 3: ОСНОВНАЯ ЛОГИКА ---
        if notification.event == "payment.succeeded":
            await payments_db.update_payment_status(payment_id, "succeeded")
            await user_courses_db.add_user_course(user_id, course_id)

            await bot.edit_message_text(
                chat_id=user_id, message_id=message_id,
                text="✅ Оплата прошла успешно! Вам открыт доступ к курсу."
            )
            logging.info(f"Payment {payment_id} succeeded for user {user_id}.")

        elif notification.event == "payment.canceled":
            await payments_db.update_payment_status(payment_id, "canceled")

            builder = InlineKeyboardBuilder()
            builder.button(text="Попробовать снова", callback_data=CourseCallbackFactory(action="buy", course_id=course_id))

            await bot.edit_message_text(
                chat_id=user_id, message_id=message_id,
                text="❌ Время оплаты истекло или платёж был отменен. Ссылка больше недействительна.",
                reply_markup=builder.as_markup()
            )
            logging.info(f"Payment {payment_id} canceled for user {user_id}.")

    except Exception as e:
        logging.error(f"Критическая ошибка при обработке вебхука от ЮKassa: {e}", exc_info=True)

    return web.Response(status=200)
