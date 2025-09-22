# handlers/user.py

import logging
from aiogram import Router, F, Bot
from aiogram.filters import CommandStart
from aiogram.types import Message, CallbackQuery, LabeledPrice, PreCheckoutQuery, SuccessfulPayment
from aiogram.utils.keyboard import InlineKeyboardBuilder

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
from config import PAYMENT_PROVIDER_TOKEN # <-- ИМПОРТИРУЕМ НОВЫЙ ТОКЕН

user_router = Router()


# --- Хендлеры каталога (остаются без изменений) ---
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
    await message.answer(
        "Доступные курсы:", reply_markup=get_courses_list_kb(courses)
    )

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


# --- НОВАЯ ЛОГИКА ПОКУПКИ ---

# 1. ЗАМЕНЯЕМ СТАРЫЙ ХЕНДЛЕР НА ЭТОТ
@user_router.callback_query(CourseCallbackFactory.filter(F.action == "buy"))
async def buy_course_handler(
    callback: CallbackQuery,
    callback_data: CourseCallbackFactory,
    bot: Bot
):
    await callback.answer() # Сразу отвечаем на нажатие кнопки

    course_id = callback_data.course_id
    course = await courses_db.get_course_by_id(course_id)

    if not course:
        await callback.message.answer("Курс не найден!")
        return

    _, title, short_desc, _, price, _ = course
    user_id = callback.from_user.id

    # Создаем запись в нашей БД, чтобы получить ID для payload
    payment_id = await payments_db.create_pending_payment(user_id, course_id, price)
    if not payment_id:
        await callback.message.answer("Произошла ошибка при создании счета.")
        return

    # Отправляем пользователю счет (инвойс)
    await bot.send_invoice(
        chat_id=user_id,
        title=title,
        description=short_desc,
        payload=f"payment_{payment_id}", # Уникальный идентификатор платежа
        provider_token=PAYMENT_PROVIDER_TOKEN,
        currency="RUB",
        prices=[
            LabeledPrice(
                label=f"Покупка курса: {title}",
                amount=int(price * 100)  # !!! ВАЖНО: Цена в копейках
            )
        ]
    )

# 2. ДОБАВЛЯЕМ НОВЫЙ ХЕНДЛЕР ДЛЯ ПОДТВЕРЖДЕНИЯ
@user_router.pre_checkout_query()
async def process_pre_checkout(pre_checkout_query: PreCheckoutQuery, bot: Bot):
    # Этот хендлер вызывается, когда пользователь нажимает "Оплатить" в окне Telegram.
    # Telegram ждет от нас подтверждения, что мы готовы принять платеж.
    await bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True)

# 3. ДОБАВЛЯЕМ НОВЫЙ ХЕНДЛЕР ДЛЯ УСПЕШНОЙ ОПЛАТЫ
@user_router.message(F.successful_payment)
async def process_successful_payment(message: Message):
    # Этот хендлер вызывается после того, как оплата прошла.

    # Получаем наш внутренний ID платежа из payload
    payment_id = int(message.successful_payment.invoice_payload.split('_')[1])

    # Находим информацию о платеже в нашей базе
    payment_info = await payments_db.get_payment_info(payment_id)
    if not payment_info:
        logging.error(f"Не найдена информация о платеже {payment_id} после успешной оплаты.")
        return

    user_id = payment_info['user_id']
    course_id = payment_info['course_id']

    # Обновляем статус в БД и выдаем курс
    await payments_db.update_payment_status(payment_id, "succeeded")
    await user_courses_db.add_user_course(user_id, course_id)

    # Отправляем пользователю подтверждение
    await message.answer("✅ Оплата прошла успешно! Вам открыт доступ к курсу. Вы можете найти его в разделе '📚 Мои курсы'.")
    logging.info(f"Платеж {payment_id} успешно завершен для пользователя {user_id}.")


# --- Хендлеры личного кабинета (остаются без изменений) ---
@user_router.callback_query(CourseCallbackFactory.filter(F.action == "back_to_list"))
async def back_to_courses_list(callback: CallbackQuery):
    courses = await courses_db.get_all_courses()
    await callback.message.edit_text(
        "Доступные курсы:", reply_markup=get_courses_list_kb(courses)
    )
    await callback.answer()

# Мои курсы
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

# История покупок

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
