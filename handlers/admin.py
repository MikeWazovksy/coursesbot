# handlers/admin.py

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from typing import List, Dict

from filters.admin import IsAdmin
from keyboards.admin_kb import (
    admin_main_kb,
    cancel_kb,
    get_admin_courses_kb,
    get_course_manage_kb,
    AdminCourseCallback,
    get_edit_field_kb,
    EditCourseCallback,
    UserPaginationCallback,
    get_users_pagination_kb,
)
from states.admin_states import AddCourse
from states.admin_states import EditCourse
from models import users as users_db
from models import courses as courses_db
from models import stats as stats_db

admin_router = Router()


@admin_router.message(Command("admin"), IsAdmin())
async def admin_panel(message: Message):
    await message.answer(
        "👋 Добро пожаловать в админ-панель!", reply_markup=admin_main_kb
    )


# Обработка отмены
@admin_router.message(F.text == "❌ Отмена")
async def cancel_action(message: Message, state: FSMContext):
    """Отменяет любое текущее действие и возвращает в главное меню."""
    current_state = await state.get_state()
    if current_state is None:
        return

    await state.clear()
    await message.answer("Действие отменено.", reply_markup=admin_main_kb)


# Добавление курса
@admin_router.message(F.text == "➕ Добавить курс", IsAdmin())
async def start_add_course(message: Message, state: FSMContext):
    await state.set_state(AddCourse.title)
    await message.answer("Введите название нового курса:", reply_markup=cancel_kb)


# Краткое описание
@admin_router.message(AddCourse.title)
async def process_title(message: Message, state: FSMContext):
    await state.update_data(title=message.text)
    await state.set_state(AddCourse.short_description)
    await message.answer("Отлично! Теперь введите краткое описание курса:")


# Полное описание
@admin_router.message(AddCourse.short_description)
async def process_short_description(message: Message, state: FSMContext):
    await state.update_data(short_description=message.text)
    await state.set_state(AddCourse.full_description)
    await message.answer(
        "Теперь введите полное описание (можно пропустить, отправив '-')"
    )


# Получаем ссылку
@admin_router.message(AddCourse.full_description)
async def process_full_description(message: Message, state: FSMContext):
    full_desc = message.text if message.text != "-" else ""
    await state.update_data(full_description=full_desc)
    await state.set_state(AddCourse.materials_link)
    await message.answer("Принято! Теперь отправьте ссылку на материалы:")


# Получаем цену
@admin_router.message(AddCourse.materials_link)
async def process_materials_link(message: Message, state: FSMContext):
    await state.update_data(materials_link=message.text)
    await state.set_state(AddCourse.price)
    await message.answer(
        "Почти готово! Укажите стоимость курса в рублях (только число):"
    )


# Сохраняем
@admin_router.message(AddCourse.price)
async def process_price(message: Message, state: FSMContext):
    try:
        price = float(message.text.replace(",", "."))
    except ValueError:
        await message.answer(
            "Неверный формат цены. Пожалуйста, введите число (например, 1990.50)."
        )
        return

    # Сохраняем все данные в БД
    course_data = await state.get_data()
    await courses_db.add_course(
        title=course_data["title"],
        short_desc=course_data["short_description"],
        full_desc=course_data["full_description"],
        link=course_data["materials_link"],
        price=price,
    )

    # Возвращаемся в главное меню
    await state.clear()
    await message.answer(
        f"✅ **Курс «{course_data['title']}» успешно добавлен!**\n\n"
        f"Цена: {price} руб.",
        reply_markup=admin_main_kb,
        parse_mode="Markdown",
    )


# Список курсов
@admin_router.message(F.text == "📋 Список курсов", IsAdmin())
async def list_courses(message: Message):
    all_courses = await courses_db.get_all_courses()
    if not all_courses:
        await message.answer("В базе данных пока нет курсов.")
        return

    await message.answer(
        "Выберите курс для управления:", reply_markup=get_admin_courses_kb(all_courses)
    )


# # Просматривает , редактируем или удаляем курс
@admin_router.callback_query(AdminCourseCallback.filter(F.action == "view"))
async def view_course(callback: CallbackQuery, callback_data: AdminCourseCallback):
    course_id = callback_data.course_id
    course = await courses_db.get_course_by_id(course_id)

    if not course:
        await callback.answer("Курс не найден!", show_alert=True)
        return

    _, title, short_desc, full_desc, price, link = course

    text = (
        f"📖 **Просмотр курса**\n\n"
        f"**ID:** {course_id}\n"
        f"**Название:** {title}\n"
        f"**Краткое описание:** {short_desc}\n"
        f"**Полное описание:** {full_desc}\n"
        f"**Цена:** {price} руб.\n"
        f"**Ссылка:** {link}"
    )

    await callback.message.edit_text(
        text,
        reply_markup=get_course_manage_kb(course_id),
        parse_mode="Markdown",
        disable_web_page_preview=True,
    )
    await callback.answer()


# Удаление курса
@admin_router.callback_query(AdminCourseCallback.filter(F.action == "delete"))
async def confirm_delete_course(
    callback: CallbackQuery, callback_data: AdminCourseCallback
):
    course_id = callback_data.course_id
    await courses_db.delete_course(course_id)

    await callback.message.edit_text("Курс был успешно удален.")
    await callback.answer("Курс удален", show_alert=True)


# Начинаем редактирование
@admin_router.callback_query(AdminCourseCallback.filter(F.action == "edit"))
async def start_edit_course(
    callback: CallbackQuery, callback_data: AdminCourseCallback, state: FSMContext
):
    course_id = callback_data.course_id
    await state.set_state(EditCourse.choosing_field)
    await state.update_data(course_id=course_id)

    await callback.message.edit_text(
        "Какое поле вы хотите отредактировать?",
        reply_markup=get_edit_field_kb(course_id),
    )
    await callback.answer()


# Обробатываем поля редактирования
@admin_router.callback_query(EditCourseCallback.filter(), EditCourse.choosing_field)
async def choose_field_to_edit(callback: CallbackQuery, callback_data: EditCourseCallback, state: FSMContext):
    await callback.answer()

    field = callback_data.field
    field_names = {
        'title': 'новое название',
        'short_description': 'новое краткое описание',
        'full_description': 'новое полное описание',
        'materials_link': 'новую ссылку на материалы',
        'price': 'новую цену'
    }

    await state.update_data(field_to_edit=field)
    await state.set_state(EditCourse.entering_new_value)

    await callback.message.delete()

    await callback.message.answer(
        f"Введите {field_names.get(field, 'новое значение')}:",
        reply_markup=cancel_kb
    )
    await callback.message.answer("...", reply_markup=cancel_kb)
    await callback.answer()


# Новое значение
@admin_router.message(EditCourse.entering_new_value)
async def process_new_value(message: Message, state: FSMContext):
    """Обновляет данные в БД и завершает процесс."""
    new_value = message.text
    data = await state.get_data()
    course_id = data.get("course_id")
    field = data.get("field_to_edit")

    # Валидация полей
    allowed_fields = [
        "title",
        "short_description",
        "full_description",
        "materials_link",
        "price",
    ]
    if field not in allowed_fields:
        await message.answer(
            "Произошла ошибка. Неверное поле для редактирования.",
            reply_markup=admin_main_kb,
        )
        await state.clear()
        return

    # Валидация цены
    if field == "price":
        try:
            new_value = float(new_value.replace(",", "."))
        except ValueError:
            await message.answer(
                "Неверный формат цены. Пожалуйста, введите число (например, 1990.50)."
            )
            return

    # Обновленям поля в бд
    await courses_db.update_course_field(course_id, field, new_value)

    await state.clear()
    await message.answer(
        f"✅ Поле **{field}** для курса **ID {course_id}** было успешно обновлено!",
        reply_markup=admin_main_kb,
        parse_mode="Markdown",
    )

    # Показываем обновления
    await view_course_after_edit(message, course_id)


async def view_course_after_edit(message: Message, course_id: int):
    course = await courses_db.get_course_by_id(course_id)
    if not course:
        return

    _, title, short_desc, full_desc, price, link = course
    text = (
        f"📖 **Обновленный курс**\n\n"
        f"**ID:** {course_id}\n"
        f"**Название:** {title}\n"
        f"**Краткое описание:** {short_desc}\n"
        f"**Полное описание:** {full_desc}\n"
        f"**Цена:** {price} руб.\n"
        f"**Ссылка:** {link}"
    )

    await message.answer(
        text,
        reply_markup=get_course_manage_kb(course_id),
        parse_mode="Markdown",
        disable_web_page_preview=True,
    )


# Статистика
@admin_router.message(F.text == "📊 Статистика", IsAdmin())
async def show_stats(message: Message):
    stats = await stats_db.get_main_stats()

    text = (
        f"📊 **Статистика бота**\n\n"
        f"👥 **Всего пользователей:** {stats['users_count']}\n"
        f"🎓 **Всего куплено курсов:** {stats['purchases_count']}\n"
        f"💰 **Успешных платежей:** {stats['successful_payments_count']} на сумму {stats['total_revenue']:.2f} руб.\n"
        f"📚 **Активных курсов в базе:** {stats['active_courses_count']}"
    )

    await message.answer(text, parse_mode="Markdown")


# Кол-во пользователей на странице
USERS_PER_PAGE = 5


async def format_users_list(users: List[Dict]) -> str:
    if not users:
        return "Пользователи не найдены."

    text = "👥 **Список пользователей:**\n\n"
    for user in users:
        text += (
            f"👤 **ID:** `{user['user_id']}`\n"
            f"   **Имя:** {user['full_name']}\n"
            f"   **Username:** @{user['username']}\n"
            f"   **Куплено курсов:** {user['courses_purchased']}\n"
            f"--------------------\n"
        )
    return text


# Список пользователей
@admin_router.message(F.text == "👥 Список юзеров", IsAdmin())
async def list_users(message: Message):
    """Отображает первую страницу списка пользователей."""
    total_users = await users_db.get_total_users_count()
    users = await users_db.get_paginated_users(limit=USERS_PER_PAGE, offset=0)

    text = await format_users_list(users)

    await message.answer(
        text,
        reply_markup=get_users_pagination_kb(
            offset=0, total_users=total_users, page_size=USERS_PER_PAGE
        ),
        parse_mode="Markdown",
    )


@admin_router.callback_query(UserPaginationCallback.filter())
async def paginate_users_list(
    callback: CallbackQuery, callback_data: UserPaginationCallback
):
    current_offset = callback_data.offset

    if callback_data.action == "next":
        new_offset = current_offset + USERS_PER_PAGE
    else:
        new_offset = current_offset - USERS_PER_PAGE

    total_users = await users_db.get_total_users_count()
    users = await users_db.get_paginated_users(limit=USERS_PER_PAGE, offset=new_offset)

    text = await format_users_list(users)

    await callback.message.edit_text(
        text,
        reply_markup=get_users_pagination_kb(
            offset=new_offset, total_users=total_users, page_size=USERS_PER_PAGE
        ),
        parse_mode="Markdown",
    )
    await callback.answer()
