import logging
import html
import asyncio
import asyncpg
from aiogram import Router, F, Bot
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import (
    Message,
    CallbackQuery,
    LabeledPrice,
    PreCheckoutQuery,
    SuccessfulPayment
)
from aiogram.utils.markdown import hbold, hlink

from keyboards.user_kb import *
from models import users as users_db
from models import courses as courses_db
from models import payments as payments_db
from models import user_courses as user_courses_db
from config import PAYMENT_PROVIDER_TOKEN, ADMIN_IDS # Добавили ADMIN_IDS

user_router = Router()


@user_router.message(CommandStart())
async def handle_start(message: Message, pool: asyncpg.Pool):
    user = message.from_user
    await users_db.add_user(
        pool, user_id=user.id, username=user.username, full_name=user.full_name
    )
    # Отправляем админскую клавиатуру админу
    if user.id in ADMIN_IDS:
        await message.answer(
            f"👋 Привет, {user.first_name}!\nВы авторизованы как администратор.",
            reply_markup=admin_main_kb,
        )
    else:
        await message.answer(
            f"👋 Привет, {user.first_name}!\nДобро пожаловать в наш бот онлайн-курсов.",
            reply_markup=main_menu_kb,
        )

@user_router.message(F.text == "🎓 Доступные курсы")
async def handle_catalog(message: Message, pool: asyncpg.Pool):
    courses = await courses_db.get_all_courses(pool)
    if not courses:
        await message.answer("К сожалению, сейчас нет доступных курсов.")
        return
    await message.answer("Доступные курсы:", reply_markup=get_courses_list_kb(courses))


@user_router.callback_query(CourseCallbackFactory.filter(F.action == "view"))
async def show_course_details(
    callback: CallbackQuery, callback_data: CourseCallbackFactory, pool: asyncpg.Pool
):
    course_id = callback_data.course_id
    course = await courses_db.get_course_by_id(pool, course_id)
    if course:
        title = html.escape(course.get('title', ''))
        full_desc = html.escape(course.get('full_description', ''))
        price = course.get('price', 0)
        text = (f"🎓 {hbold(title)}\n\n"
                f"{full_desc}\n\n"
                f"💰 {hbold('Цена:')} {price} руб.")
        await callback.message.edit_text(
            text,
            reply_markup=get_course_details_kb(course_id)
        )
    else:
        await callback.answer("Курс не найден!", show_alert=True)
    await callback.answer()

async def expire_invoice_message(
    bot: Bot, pool: asyncpg.Pool, chat_id: int, message_id: int, payment_id: int
):
    await asyncio.sleep(600)
    payment_info = await payments_db.get_payment_info(pool, payment_id)
    if payment_info and payment_info["status"] == "pending":
        try:
            await payments_db.update_payment_status(pool, payment_id, "canceled")
            await bot.delete_message(chat_id=chat_id, message_id=message_id)
            await bot.send_message(
                chat_id=chat_id,
                text=f"❌ {hbold('Время для оплаты истекло!')}\n\nДля покупки курса, пожалуйста, создайте новый счет.",
            )
        except Exception as e:
            logging.error(f"Не удалось обработать истекший счет (payment_id: {payment_id}): {e}")

@user_router.callback_query(CourseCallbackFactory.filter(F.action == "buy"))
async def buy_course_handler(
    callback: CallbackQuery, callback_data: CourseCallbackFactory, bot: Bot, pool: asyncpg.Pool
):
    await callback.answer()
    course_id = callback_data.course_id
    course = await courses_db.get_course_by_id(pool, course_id)
    if not course:
        await callback.message.answer("Курс не найден!")
        return

    title = html.escape(course.get('title', ''))
    short_desc = html.escape(course.get('short_description', ''))
    price = course.get('price', 0)
    user_id = callback.from_user.id

    payment_id = await payments_db.create_pending_payment(pool, user_id, course_id, price)
    if not payment_id:
        await callback.message.answer("Произошла ошибка при создании счета.")
        return

    try:
        invoice_message = await bot.send_invoice(
            chat_id=user_id,
            title=title,
            description=short_desc,
            payload=f"payment_{payment_id}",
            provider_token=PAYMENT_PROVIDER_TOKEN,
            currency="RUB",
            prices=[LabeledPrice(label=f"Покупка курса: {title}", amount=int(price * 100))]
        )
        asyncio.create_task(
            expire_invoice_message(
                bot, pool, invoice_message.chat.id, invoice_message.message_id, payment_id
            )
        )
    except Exception as e:
        await callback.message.answer("Произошла ошибка при отправке счета.")
        logging.error(f"Ошибка при отправке инвойса: {e}")

@user_router.pre_checkout_query()
async def process_pre_checkout(pre_checkout_query: PreCheckoutQuery, bot: Bot, pool: asyncpg.Pool):
    payload = pre_checkout_query.invoice_payload
    try:
        payment_id = int(payload.split("_")[1])
    except (ValueError, IndexError):
        await bot.answer_pre_checkout_query(
            pre_checkout_query.id, ok=False, error_message="Неверный ID платежа."
        )
        return

    payment_info = await payments_db.get_payment_info(pool, payment_id)
    if not payment_info or payment_info["status"] != "pending":
        await bot.answer_pre_checkout_query(
            pre_checkout_query.id, ok=False,
            error_message="Срок действия счета истек. Пожалуйста, создайте новый счет.",
        )
        return
    await bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True)

@user_router.message(F.successful_payment)
async def process_successful_payment(message: Message, pool: asyncpg.Pool):
    payment_id = int(message.successful_payment.invoice_payload.split("_")[1])
    payment_info = await payments_db.get_payment_info(pool, payment_id)
    if not payment_info:
        logging.error(f"Не найдена информация о платеже {payment_id} после успешной оплаты.")
        return

    user_id = payment_info["user_id"]
    course_id = payment_info["course_id"]
    await payments_db.update_payment_status(pool, payment_id, "succeeded")
    await user_courses_db.add_user_course(pool, user_id, course_id)
    await message.answer("✅ Оплата прошла успешно! Вам открыт доступ к курсу.")
    logging.info(f"Платеж {payment_id} успешно завершен для пользователя {user_id}.")


@user_router.callback_query(CourseCallbackFactory.filter(F.action == "back_to_list"))
async def back_to_courses_list(callback: CallbackQuery, pool: asyncpg.Pool):
    courses = await courses_db.get_all_courses(pool)
    await callback.message.edit_text(
        "Доступные курсы:", reply_markup=get_courses_list_kb(courses)
    )
    await callback.answer()

@user_router.message(F.text == "📚 Мои курсы")
async def handle_my_courses(message: Message, pool: asyncpg.Pool):
    user_id = message.from_user.id
    my_courses = await user_courses_db.get_user_courses_with_details(pool, user_id)
    if not my_courses:
        await message.answer("У вас пока нет купленных курсов.")
        return
    response_text = f"📚 {hbold('Ваши курсы:')}\n\n"
    for course in my_courses:
        title = html.escape(course['title'])
        link = hlink('Ссылка на материалы', course['materials_link'])
        response_text += f"🎓 {hbold(title)}\n🔗 {link}\n\n"
    await message.answer(response_text, disable_web_page_preview=True)

@user_router.message(F.text == "🧾 История покупок")
async def handle_purchase_history(message: Message, pool: asyncpg.Pool):
    user_id = message.from_user.id
    history = await payments_db.get_user_payment_history(pool, user_id)
    if not history:
        await message.answer("Ваша история покупок пуста.")
        return
    response_text = f"🧾 {hbold('История ваших покупок:')}\n\n"
    status_map = {"succeeded": "✅ Успешно", "pending": "⏳ В ожидании", "canceled": "❌ Отменен"}
    for payment in history:
        status_emoji = status_map.get(payment["status"], "❓")
        title = html.escape(payment['title'])
        amount_decimal = payment['amount']
        amount_formatted = f"{amount_decimal:0.2f}".rstrip('0').rstrip('.')

        response_text += (
            f"{hbold('Курс:')} {title}\n"
            f"{hbold('Сумма:')} {amount_formatted} руб.\n"
            f"{hbold('Дата:')} {payment['payment_date'].strftime('%Y-%m-%d %H:%M')}\n"
            f"{hbold('Статус:')} {status_emoji}\n\n"
        )
    await message.answer(response_text)
