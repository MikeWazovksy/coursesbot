import logging
from aiogram import Router, F, Bot
from aiogram.filters import CommandStart
from aiogram.types import Message, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder

# --- Импорты ---
from keyboards.user_kb import (
    main_menu_kb,
    get_courses_list_kb,
    get_course_details_kb,
    CourseCallbackFactory,
)
from models import users as users_db
from models import courses as courses_db

from services import payments as payment_service
from models import payments as payments_db
from models import user_courses as user_courses_db


user_router = Router()


# Приветствие
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


# Доступность курсов
@user_router.message(F.text == "🎓 Доступные курсы")
async def handle_catalog(message: Message):
    courses = await courses_db.get_all_courses()
    if not courses:
        await message.answer("К сожалению, сейчас нет доступных курсов.")
        return
    await message.answer(
        "Доступные курсы:", reply_markup=get_courses_list_kb(courses)
    )


# Цена курса
@user_router.callback_query(CourseCallbackFactory.filter(F.action == "view"))
async def show_course_details(
    callback: CallbackQuery, callback_data: CourseCallbackFactory
):
    course_id = callback_data.course_id
    course = await courses_db.get_course_by_id(course_id)
    if course:
        _, title, short_desc, full_desc, price, link = course
        text = f"🎓 **{title}**\n\n{full_desc}\n\n💰 **Цена:** {price} руб."
        await callback.message.edit_text(
            text, reply_markup=get_course_details_kb(course_id), parse_mode="Markdown"
        )
    else:
        await callback.answer("Курс не найден!", show_alert=True)
    await callback.answer()


# Кнопка купить
@user_router.callback_query(CourseCallbackFactory.filter(F.action == "buy"))
async def buy_course_handler(
    callback: CallbackQuery,
    callback_data: CourseCallbackFactory,
    bot: Bot
):
    logging.warning("--- ЗАПУЩЕН НОВЫЙ buy_course_handler ---")
    course_id = callback_data.course_id
    course = await courses_db.get_course_by_id(course_id)

    if not course:
        await callback.answer("Курс не найден!", show_alert=True)
        return

    _, title, _, _, price, _ = course
    user_id = callback.from_user.id

    payment_id = await payments_db.create_pending_payment(user_id, course_id, price)
    if not payment_id:
        await callback.message.answer("Произошла ошибка при создании платежа.")
        await callback.answer()
        return

    temp_message = await callback.message.edit_text("Минутку, генерирую ссылку на оплату...")
    message_id = temp_message.message_id

    await payments_db.update_payment_message_id(payment_id, message_id)

    # УБЕДИТЕСЬ, ЧТО METADATA СОБИРАЕТСЯ ИМЕННО ТАК
    metadata = {
        "payment_id": payment_id,
        "user_id": user_id,
        "course_id": course_id,
        "message_id": message_id
    }

    payment_url, yookassa_payment_id = await payment_service.create_payment(
        amount=price, description=f"Покупка курса: {title}", metadata=metadata
    )

    builder = InlineKeyboardBuilder()
    builder.button(text="➡️ Оплатить", url=payment_url)

    await bot.edit_message_text(
        chat_id=user_id,
        message_id=message_id,
        text=(f"Вы собираетесь купить курс «**{title}**» за **{price}** руб.\n\n"
              "Нажмите на кнопку ниже. Ссылка действительна 10 минут."),
        reply_markup=builder.as_markup(),
        parse_mode="Markdown"
    )

    await callback.answer()


# Доступность курсов
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
