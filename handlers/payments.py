# handlers/payments.py

import logging
import asyncio
from aiohttp import web
from aiogram import Bot
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.exceptions import TelegramBadRequest
from yookassa.domain.notification import WebhookNotification

# --- Убедитесь, что эти импорты на месте ---
from models import payments as payments_db
from models import user_courses as user_courses_db
from keyboards.user_kb import CourseCallbackFactory
from config import ADMIN_IDS # <-- ДОБАВЛЕННЫЙ ИМПОРТ

# --- ДИАГНОСТИЧЕСКАЯ ВЕРСИЯ ОБРАБОТЧИКА ---
async def yookassa_webhook_handler(request: web.Request) -> web.Response:
    bot: Bot = request.app["bot"]
    admin_to_notify = ADMIN_IDS[0] # Берем ID первого админа из списка

    try:
        # --- ШАГ 1: Отправляем сигнал о том, что функция НАЧАЛАСЬ ---
        await bot.send_message(admin_to_notify, "!!! ВЕБХУК ОТ ЮKASSA ПОЛУЧЕН !!!")

        data = await request.json()

        # --- ШАГ 2: Отправляем полученные данные для анализа ---
        await bot.send_message(admin_to_notify, f"Данные: {str(data)}")

        notification = WebhookNotification(data)
        # ... (здесь мог бы быть остальной код, но для теста он не нужен)

        # --- ШАГ 3: Отправляем сигнал, что всё прошло без ошибок ---
        await bot.send_message(admin_to_notify, "Обработка данных прошла без падения.")

    except Exception as e:
        # --- ШАГ 4: Если что-то сломалось, отправляем ошибку ---
        logging.error(f"Критическая ошибка при обработке вебхука: {e}", exc_info=True)
        await bot.send_message(admin_to_notify, f"!!! ОШИБКА В ОБРАБОТЧИКЕ: {e} !!!")

    return web.Response(status=200)
