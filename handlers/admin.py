import html
import asyncpg
from typing import List, Dict
from aiogram import F, Bot, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from aiogram.utils.markdown import hbold, hcode, hlink

from filters.admin import IsAdmin
from keyboards.admin_kb import *
from models import courses as courses_db
from models import stats as stats_db
from models import users as users_db
from models import settings as settings_db
from states.admin_states import AddCourse, EditCourse, EditWelcomeMessage

admin_router = Router()


@admin_router.message(Command("admin"), IsAdmin())
async def admin_panel(message: Message):
    await message.answer(
        "👋 Добро пожаловать в админ-панель!", reply_markup=admin_main_kb
    )


@admin_router.message(F.text == "❌ Отмена")
async def cancel_action(message: Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state is None:
        return
    await state.clear()
    await message.answer("Действие отменено.", reply_markup=admin_main_kb)


@admin_router.message(F.text == "➕ Добавить курс", IsAdmin())
async def start_add_course(message: Message, state: FSMContext):
    await state.set_state(AddCourse.title)
    await message.answer("Введите название нового курса:", reply_markup=cancel_kb)


@admin_router.message(AddCourse.title)
async def process_title(message: Message, state: FSMContext):
    await state.update_data(title=message.text)
    await state.set_state(AddCourse.short_description)
    await message.answer("Отлично! Теперь введите краткое описание курса:")


@admin_router.message(AddCourse.short_description)
async def process_short_description(message: Message, state: FSMContext):
    await state.update_data(short_description=message.text)
    await state.set_state(AddCourse.full_description)
    await message.answer(
        "Отлично! Теперь введите полное описание (можно пропустить, отправив '-')"
    )


@admin_router.message(AddCourse.full_description)
async def process_full_description(message: Message, state: FSMContext):
    full_desc = message.text if message.text != "-" else ""
    await state.update_data(full_description=full_desc)
    await state.set_state(AddCourse.materials_link)
    await message.answer("Отлично! Теперь отправьте ссылку на материалы:")


@admin_router.message(AddCourse.materials_link)
async def process_materials_link(message: Message, state: FSMContext):
    await state.update_data(materials_link=message.text)
    await state.set_state(AddCourse.price)
    await message.answer(
        "Почти готово! Укажите стоимость курса в рублях (только число):"
    )


@admin_router.message(AddCourse.price)
async def process_price(message: Message, state: FSMContext, pool: asyncpg.Pool):
    try:
        price = float(message.text.replace(",", "."))
    except ValueError:
        await message.answer("Неверный формат цены. Введите число (например, 1990.50).")
        return

    course_data = await state.get_data()
    await courses_db.add_course(
        pool,
        title=course_data["title"],
        short_desc=course_data["short_description"],
        full_desc=course_data["full_description"],
        link=course_data["materials_link"],
        price=price,
    )
    await state.clear()
    title = html.escape(course_data.get("title", ""))
    text = f"✅ Курс «{hbold(title)}» успешно добавлен!\n\nЦена: {price} руб."
    await message.answer(text, reply_markup=admin_main_kb)


COURSES_PER_PAGE = 5


@admin_router.message(F.text == "📋 Список курсов", IsAdmin())
async def list_courses(message: Message, pool: asyncpg.Pool):
    total_courses = await courses_db.get_total_courses_count(pool)
    courses = await courses_db.get_paginated_courses(
        pool, limit=COURSES_PER_PAGE, offset=0
    )

    if not courses:
        await message.answer("Активных курсов в базе данных пока нет.")
        return

    await message.answer(
        "Управление активными курсами:",
        reply_markup=get_admin_courses_kb(
            courses, offset=0, total_courses=total_courses, page_size=COURSES_PER_PAGE
        ),
    )


@admin_router.callback_query(AdminCoursePaginationCallback.filter())
async def paginate_courses_list(
    callback: CallbackQuery,
    callback_data: AdminCoursePaginationCallback,
    pool: asyncpg.Pool,
):
    current_offset = callback_data.offset
    if callback_data.action == "next":
        new_offset = current_offset + COURSES_PER_PAGE
    else:
        new_offset = current_offset - COURSES_PER_PAGE

    total_courses = await courses_db.get_total_courses_count(pool)
    courses = await courses_db.get_paginated_courses(
        pool, limit=COURSES_PER_PAGE, offset=new_offset
    )

    await callback.message.edit_text(
        "Управление активными курсами:",
        reply_markup=get_admin_courses_kb(
            courses,
            offset=new_offset,
            total_courses=total_courses,
            page_size=COURSES_PER_PAGE,
        ),
    )
    await callback.answer()


def _format_course_details_text(course: Dict, course_id: int, title_prefix: str) -> str:
    title = html.escape(course.get("title", ""))
    short_desc = html.escape(course.get("short_description", ""))
    full_desc = html.escape(course.get("full_description", ""))
    price = course.get("price", 0)
    link = hlink("Ссылка", course.get("materials_link", ""))
    is_active = course.get("is_active", False)
    status = "✅ Активен" if is_active else "🗄️ В архиве"

    return (
        f"📖 {hbold(title_prefix)}\n\n"
        f"{hbold('ID:')} {hcode(course_id)}\n"
        f"{hbold('Статус:')} {status}\n"
        f"{hbold('Название:')} {title}\n"
        f"{hbold('Краткое описание:')} {short_desc}\n"
        f"{hbold('Полное описание:')} {full_desc}\n"
        f"{hbold('Цена:')} {price} руб.\n"
        f"{hbold('Ссылка:')} {link}"
    )


@admin_router.callback_query(AdminCourseCallback.filter(F.action == "view"))
async def view_course(
    callback: CallbackQuery, callback_data: AdminCourseCallback, pool: asyncpg.Pool
):
    await callback.answer()
    course_id = callback_data.course_id
    course = await courses_db.get_course_by_id(pool, course_id)
    if not course:
        await callback.answer("Курс не найден!", show_alert=True)
        return

    text = _format_course_details_text(course, course_id, "Просмотр курса")

    is_active = course.get("is_active", False)
    reply_markup = (
        get_course_manage_kb(course_id)
        if is_active
        else get_archived_course_manage_kb(course_id)
    )

    await callback.message.edit_text(
        text,
        reply_markup=reply_markup,
        disable_web_page_preview=True,
    )


@admin_router.callback_query(AdminCourseCallback.filter(F.action == "delete"))
async def confirm_delete_course(
    callback: CallbackQuery, callback_data: AdminCourseCallback
):
    await callback.message.edit_text(
        "Вы уверены, что хотите архивировать этот курс?",
        reply_markup=get_confirm_delete_kb(callback_data.course_id),
    )
    await callback.answer()


@admin_router.callback_query(AdminCourseCallback.filter(F.action == "confirm_delete"))
async def delete_course_confirmed(
    callback: CallbackQuery, callback_data: AdminCourseCallback, pool: asyncpg.Pool
):
    course_id = callback_data.course_id
    await courses_db.delete_course(pool, course_id)
    await callback.message.edit_text("✅ Курс был успешно архивирован.")
    await callback.answer()


@admin_router.callback_query(AdminCourseCallback.filter(F.action == "back_to_list"))
async def back_to_course_list_admin(callback: CallbackQuery, pool: asyncpg.Pool):
    total_courses = await courses_db.get_total_courses_count(pool)
    courses = await courses_db.get_paginated_courses(
        pool, limit=COURSES_PER_PAGE, offset=0
    )

    await callback.message.edit_text(
        "Выберите курс для управления:",
        reply_markup=get_admin_courses_kb(
            courses, offset=0, total_courses=total_courses, page_size=COURSES_PER_PAGE
        ),
    )
    await callback.answer()


@admin_router.callback_query(
    AdminCourseCallback.filter(F.action == "back_to_main_menu")
)
async def back_to_main_menu_admin(callback: CallbackQuery):
    await callback.message.delete()
    await callback.message.answer(
        "Вы вернулись в главное меню.", reply_markup=admin_main_kb
    )
    await callback.answer()


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


@admin_router.callback_query(EditCourseCallback.filter(), EditCourse.choosing_field)
async def choose_field_to_edit(
    callback: CallbackQuery, callback_data: EditCourseCallback, state: FSMContext
):
    await callback.answer()
    field = callback_data.field
    field_names = {
        "title": "новое название",
        "short_description": "новое краткое описание",
        "full_description": "новое полное описание",
        "materials_link": "новую ссылку",
        "price": "новую цену",
    }
    await state.update_data(field_to_edit=field)
    await state.set_state(EditCourse.entering_new_value)
    await callback.message.delete()
    await callback.message.answer(
        f"Введите {field_names.get(field, 'новое значение')}:", reply_markup=cancel_kb
    )


@admin_router.message(EditCourse.entering_new_value)
async def process_new_value(message: Message, state: FSMContext, pool: asyncpg.Pool):
    new_value = message.text
    data = await state.get_data()
    course_id = data.get("course_id")
    field = data.get("field_to_edit")

    if field == "price":
        try:
            new_value = float(new_value.replace(",", "."))
        except ValueError:
            await message.answer(
                "Неверный формат цены. Введите число (например, 1990.50)."
            )
            return

    await courses_db.update_course_field(pool, course_id, field, new_value)
    await state.clear()

    display_field_names = {
        "title": "Название",
        "short_description": "Краткое описание",
        "full_description": "Полное описание",
        "materials_link": "Ссылка",
        "price": "Цена",
    }
    display_name = display_field_names.get(field, field)
    text = f"✅ Поле {hbold(display_name)} для курса {hbold('ID ' + str(course_id))} было обновлено!"
    await message.answer(text, reply_markup=admin_main_kb)

    course = await courses_db.get_course_by_id(pool, course_id)
    if course:
        text = _format_course_details_text(course, course_id, "Обновленный курс")
        await message.answer(
            text,
            reply_markup=get_course_manage_kb(course_id),
            disable_web_page_preview=True,
        )


@admin_router.message(F.text == "📊 Статистика", IsAdmin())
async def show_stats(message: Message, pool: asyncpg.Pool):
    stats = await stats_db.get_main_stats(pool)
    text = (
        f"📊 {hbold('Статистика бота')}\n\n"
        f"👥 {hbold('Всего пользователей:')} {stats['users_count']}\n"
        f"🎓 {hbold('Всего куплено курсов:')} {stats['purchases_count']}\n"
        f"💰 {hbold('Успешных платежей:')} {stats['successful_payments_count']} на сумму {stats['total_revenue']:.2f} руб.\n"
        f"📚 {hbold('Активных курсов в базе:')} {stats['active_courses_count']}"
    )
    await message.answer(text)


USERS_PER_PAGE = 5


async def format_users_list(users: List[Dict]) -> str:
    if not users:
        return "Пользователи не найдены."
    text = f"{hbold('👥 Список пользователей:')}\n\n"
    for user in users:
        user_id = user["user_id"]
        full_name = html.escape(str(user["full_name"] or "Без имени"))
        username = html.escape(str(user["username"] or "Без юзернейма"))
        courses_purchased = user["courses_purchased"]
        text += (
            f"👤 {hbold('ID:')} {hcode(user_id)}\n"
            f"   {hbold('Имя:')} {full_name}\n"
            f"   {hbold('Username:')} @{username}\n"
            f"   {hbold('Куплено курсов:')} {courses_purchased}\n"
            f"--------------------"
        )
    return text


@admin_router.message(F.text == "👥 Список юзеров", IsAdmin())
async def list_users(message: Message, pool: asyncpg.Pool):
    total_users = await users_db.get_total_users_count(pool)
    users = await users_db.get_paginated_users(pool, limit=USERS_PER_PAGE, offset=0)
    text = await format_users_list(users)
    await message.answer(
        text,
        reply_markup=get_users_pagination_kb(
            offset=0, total_users=total_users, page_size=USERS_PER_PAGE
        ),
    )


@admin_router.callback_query(UserPaginationCallback.filter())
async def paginate_users_list(
    callback: CallbackQuery, callback_data: UserPaginationCallback, pool: asyncpg.Pool
):
    current_offset = callback_data.offset
    if callback_data.action == "next":
        new_offset = current_offset + USERS_PER_PAGE
    else:
        new_offset = current_offset - USERS_PER_PAGE
    total_users = await users_db.get_total_users_count(pool)
    users = await users_db.get_paginated_users(
        pool, limit=USERS_PER_PAGE, offset=new_offset
    )
    text = await format_users_list(users)
    await callback.message.edit_text(
        text,
        reply_markup=get_users_pagination_kb(
            offset=new_offset, total_users=total_users, page_size=USERS_PER_PAGE
        ),
    )
    await callback.answer()


@admin_router.message(F.text == "✏️ Изменить приветствие", IsAdmin())
async def start_edit_welcome_message(
    message: Message, state: FSMContext, pool: asyncpg.Pool
):
    current_welcome_message = await settings_db.get_setting(pool, "welcome_message")
    if current_welcome_message:
        await message.answer(
            f"Текущее приветствие:\n\n{current_welcome_message}\n\nОтправьте новое сообщение.",
            reply_markup=cancel_kb,
        )
    else:
        await message.answer(
            "Приветственное сообщение еще не установлено. Отправьте его.",
            reply_markup=cancel_kb,
        )
    await state.set_state(EditWelcomeMessage.entering_message)


@admin_router.message(EditWelcomeMessage.entering_message)
async def process_new_welcome_message(
    message: Message, state: FSMContext, pool: asyncpg.Pool
):
    await settings_db.set_setting(pool, "welcome_message", message.text)
    await state.clear()
    await message.answer(
        "✅ Приветственное сообщение успешно обновлено!",
        reply_markup=admin_main_kb,
    )


@admin_router.message(F.text == "🗄️ Архив курсов", IsAdmin())
async def list_archived_courses(message: Message, pool: asyncpg.Pool):
    total_courses = await courses_db.get_total_archived_courses_count(pool)
    courses = await courses_db.get_paginated_archived_courses(
        pool, limit=COURSES_PER_PAGE, offset=0
    )

    if not courses:
        await message.answer("В архиве пока нет курсов.")
        return

    await message.answer(
        "Управление архивными курсами:",
        reply_markup=get_admin_archived_courses_kb(  # Нужна новая функция для клавиатуры
            courses, offset=0, total_courses=total_courses, page_size=COURSES_PER_PAGE
        ),
    )


@admin_router.callback_query(
    AdminArchivedCoursePaginationCallback.filter()
)  # Нужен новый CallbackFactory
async def paginate_archived_courses_list(
    callback: CallbackQuery,
    callback_data: AdminArchivedCoursePaginationCallback,
    pool: asyncpg.Pool,
):
    current_offset = callback_data.offset
    if callback_data.action == "next":
        new_offset = current_offset + COURSES_PER_PAGE
    else:
        new_offset = current_offset - COURSES_PER_PAGE

    total_courses = await courses_db.get_total_archived_courses_count(pool)
    courses = await courses_db.get_paginated_archived_courses(
        pool, limit=COURSES_PER_PAGE, offset=new_offset
    )

    await callback.message.edit_text(
        "Управление архивными курсами:",
        reply_markup=get_admin_archived_courses_kb(
            courses,
            offset=new_offset,
            total_courses=total_courses,
            page_size=COURSES_PER_PAGE,
        ),
    )
    await callback.answer()


@admin_router.callback_query(AdminCourseCallback.filter(F.action == "restore"))
async def restore_course(
    callback: CallbackQuery, callback_data: AdminCourseCallback, pool: asyncpg.Pool
):
    course_id = callback_data.course_id
    await courses_db.update_course_field(pool, course_id, "is_active", True)
    await callback.message.edit_text(
        f"✅ Курс с ID {course_id} успешно восстановлен из архива!"
    )
    await callback.answer()


@admin_router.callback_query(
    AdminCourseCallback.filter(F.action == "back_to_archive_list")
)
async def back_to_archive_list_admin(callback: CallbackQuery, pool: asyncpg.Pool):
    await callback.answer()
    total_courses = await courses_db.get_total_archived_courses_count(pool)
    courses = await courses_db.get_paginated_archived_courses(
        pool, limit=COURSES_PER_PAGE, offset=0
    )

    if not courses:
        await callback.message.edit_text("В архиве пока нет курсов.")
        return

    await callback.message.edit_text(
        "Управление архивными курсами:",
        reply_markup=get_admin_archived_courses_kb(
            courses, offset=0, total_courses=total_courses, page_size=COURSES_PER_PAGE
        ),
    )
