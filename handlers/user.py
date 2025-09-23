# handlers/user.py

import logging
from aiogram import Router, F, Bot
from aiogram.filters import CommandStart
from aiogram.types import (
    Message,
    CallbackQuery,
    LabeledPrice,
    PreCheckoutQuery,
    SuccessfulPayment,
)
from aiogram.utils.keyboard import InlineKeyboardBuilder
from datetime import datetime, timedelta
import asyncio

# --- Импорты из нашего проекта ---
from keyboards.user_kb import (
    main_menu_kb,
    get_courses_list_kb,
    get_course_details_kb,
    CourseCallbackFactory,
)
from models import users as users_db
from models import courses as courses_db
from models import payments as payments_db
from models import user_courses as user_courses_db
from config import PAYMENT_PROVIDER_TOKEN

user_router = Router()


@user_router.message(CommandStart())
async def handle_start(message: Message):
    user = message.from_user
    await users_db.add_user(
        user_id=user.id, username=user.username, full_name=user.full_name
    )
    await message.answer(
        f"👋 Привет, {user.first_name}!\nДобро пожаловать в наш бот онлайн-курсов.",
        reply_markup=main_menu_kb,
    )


@user_router.message(F.text == "🎓 Доступные курсы")
async def handle_catalog(message: Message):
    courses = await courses_db.get_all_courses()
    if not courses:
        await message.answer("К сожалению, сейчас нет доступных курсов.")
        return
    await message.answer("Доступные курсы:", reply_markup=get_courses_list_kb(courses))


@user_router.callback_query(CourseCallbackFactory.filter(F.action == "view"))
async def show_course_details(
    callback: CallbackQuery, callback_data: CourseCallbackFactory
):
    course_id = callback_data.course_id
    course = await courses_db.get_course_by_id(course_id)
    if course:
        _, title, _, full_desc, price, _ = course
        text = f"🎓 **{title}**\n\n{full_desc}\n\n💰 **Цена:** {price} руб."
        await callback.message.edit_text(
            text, reply_markup=get_course_details_kb(course_id), parse_mode="Markdown"
        )
    else:
        await callback.answer("Курс не найден!", show_alert=True)
    await callback.answer()


# --- ИСПРАВЛЕННАЯ ФУНКЦИЯ ДЛЯ ТАЙМЕРА ---
async def expire_invoice_message(
    bot: Bot, chat_id: int, message_id: int, payment_id: int
):
    """
    Отложенная функция, которая проверяет, и удаляет просроченный счет.
    """
    # Ждём 10 минут, пока счет действителен
    await asyncio.sleep(600)  # 600 секунд = 10 минут

    # Проверяем статус платежа в нашей БД
    payment_info = await payments_db.get_payment_info(payment_id)

    # Если платеж все еще в статусе 'pending' (не оплачен)
    if payment_info and payment_info["status"] == "pending":
        try:
            # Обновляем статус на 'canceled'
            await payments_db.update_payment_status(payment_id, "canceled")

            # Удаляем старое сообщение с инвойсом
            await bot.delete_message(chat_id=chat_id, message_id=message_id)

            # Отправляем новое сообщение
            await bot.send_message(
                chat_id=chat_id,
                text="❌ **Время для оплаты истекло!**\n\nДля покупки курса создайте новый счет.",
                parse_mode="Markdown",
            )
        except Exception as e:
            logging.error(f"Не удалось удалить или отправить сообщение: {e}")


# --- ИСПРАВЛЕННЫЙ ХЕНДЛЕР ПОКУПКИ ---
@user_router.callback_query(CourseCallbackFactory.filter(F.action == "buy"))
async def buy_course_handler(
    callback: CallbackQuery, callback_data: CourseCallbackFactory, bot: Bot
):
    await callback.answer()

    course_id = callback_data.course_id
    course = await courses_db.get_course_by_id(course_id)

    if not course:
        await callback.message.answer("Курс не найден!")
        return

    _, title, short_desc, _, price, _ = course
    user_id = callback.from_user.id

    payment_id = await payments_db.create_pending_payment(user_id, course_id, price)
    if not payment_id:
        await callback.message.answer("Произошла ошибка при создании счета.")
        return

    try:
        # Отправляем инвойс и сохраняем его Message ID
        invoice_message = await bot.send_invoice(
            chat_id=user_id,
            title=title,
            description=short_desc,
            payload=f"payment_{payment_id}",
            provider_token=PAYMENT_PROVIDER_TOKEN,
            currency="RUB",
            prices=[
                LabeledPrice(label=f"Покупка курса: {title}", amount=int(price * 100))
            ],
        )

        # Запускаем отложенную задачу для удаления через 10 минут
        asyncio.create_task(
            expire_invoice_message(
                bot, invoice_message.chat.id, invoice_message.message_id, payment_id
            )
        )
    except Exception as e:
        await callback.message.answer("Произошла ошибка при отправке счета.")
        logging.error(f"Ошибка при отправке инвойса: {e}")


# --- БЕЗ ИЗМЕНЕНИЙ ---
@user_router.pre_checkout_query()
async def process_pre_checkout(pre_checkout_query: PreCheckoutQuery, bot: Bot):
    payload = pre_checkout_query.invoice_payload
    try:
        payment_id = int(payload.split("_")[1])
    except (ValueError, IndexError):
        await bot.answer_pre_checkout_query(
            pre_checkout_query.id, ok=False, error_message="Неверный ID платежа."
        )
        return

    payment_info = await payments_db.get_payment_info(payment_id)

    if not payment_info or payment_info["status"] == "canceled":
        await bot.answer_pre_checkout_query(
            pre_checkout_query.id,
            ok=False,
            error_message="Срок действия счета истек. Пожалуйста, создайте новый счет.",
        )
        return

    await bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True)


@user_router.message(F.successful_payment)
async def process_successful_payment(message: Message):
    payment_id = int(message.successful_payment.invoice_payload.split("_")[1])

    payment_info = await payments_db.get_payment_info(payment_id)
    if not payment_info:
        logging.error(
            f"Не найдена информация о платеже {payment_id} после успешной оплаты."
        )
        return

    user_id = payment_info["user_id"]
    course_id = payment_info["course_id"]

    await payments_db.update_payment_status(payment_id, "succeeded")
    await user_courses_db.add_user_course(user_id, course_id)

    await message.answer(
        "✅ Оплата прошла успешно! Вам открыт доступ к курсу. Вы можете найти его в разделе '📚 Мои курсы'."
    )
    logging.info(f"Платеж {payment_id} успешно завершен для пользователя {user_id}.")


@user_router.callback_query(CourseCallbackFactory.filter(F.action == "back_to_list"))
async def back_to_courses_list(callback: CallbackQuery):
    courses = await courses_db.get_all_courses()
    await callback.message.edit_text(
        "Доступные курсы:", reply_markup=get_courses_list_kb(courses)
    )
    await callback.answer()


@user_router.message(F.text == "📚 Мои курсы")
async def handle_my_courses(message: Message):
    user_id = message.from_user.id
    my_courses = await user_courses_db.get_user_courses_with_details(user_id)

    if not my_courses:
        await message.answer("У вас пока нет купленных курсов.")
        return

    response_text = "📚 **Ваши курсы:**\n\n"
    for course in my_courses:
        response_text += f"🎓 **{course['title']}**\n🔗 Ссылка на материалы курса: {course['materials_link']}\n\n"

    await message.answer(
        response_text, parse_mode="Markdown", disable_web_page_preview=True
    )


@user_router.message(F.text == "🧾 История покупок")
async def handle_purchase_history(message: Message):
    user_id = message.from_user.id
    history = await payments_db.get_user_payment_history(user_id)

    if not history:
        await message.answer("Ваша история покупок пуста.")
        return

    response_text = "🧾 **История ваших покупок:**\n\n"
    status_map = {
        "succeeded": "✅ Успешно",
        "pending": "⏳ В ожидании",
        "canceled": "❌ Отменен",
    }
    for payment in history:
        status_emoji = status_map.get(payment["status"], "❓")
        response_text += (
            f"**Курс:** {payment['title']}\n"
            f"**Сумма:** {payment['amount']} руб.\n"
            f"**Дата:** {payment['payment_date']}\n"
            f"**Статус:** {status_emoji}\n\n"
        )

    await message.answer(response_text, parse_mode="Markdown")
