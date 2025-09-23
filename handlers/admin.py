import html
from typing import List, Dict
from aiogram import F, Bot, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from aiogram.utils.markdown import hbold, hcode, hlink

from filters.admin import IsAdmin
from keyboards.admin_kb import (
    AdminCourseCallback,
    EditCourseCallback,
    UserPaginationCallback,
    admin_main_kb,
    cancel_kb,
    get_admin_courses_kb,
    get_course_manage_kb,
    get_edit_field_kb,
    get_users_pagination_kb,
)
from models import courses as courses_db
from models import stats as stats_db
from models import users as users_db
from states.admin_states import AddCourse, EditCourse

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
async def process_price(message: Message, state: FSMContext):
    try:
        price = float(message.text.replace(",", "."))
    except ValueError:
        await message.answer("Неверный формат цены. Введите число (например, 1990.50).")
        return

    course_data = await state.get_data()
    await courses_db.add_course(
        title=course_data["title"],
        short_desc=course_data["short_description"],
        full_desc=course_data["full_description"],
        link=course_data["materials_link"],
        price=price,
    )
    await state.clear()

    title = html.escape(course_data.get('title', ''))
    text = f"✅ Курс «{hbold(title)}» успешно добавлен!\n\nЦена: {price} руб."
    await message.answer(text, reply_markup=admin_main_kb)


@admin_router.message(F.text == "📋 Список курсов", IsAdmin())
async def list_courses(message: Message):
    all_courses = await courses_db.get_all_courses()
    if not all_courses:
        await message.answer("В базе данных пока нет курсов.")
        return
    await message.answer(
        "Выберите курс для управления:", reply_markup=get_admin_courses_kb(all_courses)
    )

@admin_router.callback_query(AdminCourseCallback.filter(F.action == "view"))
async def view_course(callback: CallbackQuery, callback_data: AdminCourseCallback):
    course_id = callback_data.course_id
    course = await courses_db.get_course_by_id(course_id)
    if not course:
        await callback.answer("Курс не найден!", show_alert=True)
        return

    title = html.escape(course.get('title', ''))
    short_desc = html.escape(course.get('short_description', ''))
    full_desc = html.escape(course.get('full_description', ''))
    price = course.get('price', 0)
    link = hlink('Ссылка', course.get('materials_link', ''))

    text = (
        f"📖 {hbold('Просмотр курса')}\n\n"
        f"{hbold('ID:')} {hcode(course_id)}\n"
        f"{hbold('Название:')} {title}\n"
        f"{hbold('Краткое описание:')} {short_desc}\n"
        f"{hbold('Полное описание:')} {full_desc}\n"
        f"{hbold('Цена:')} {price} руб.\n"
        f"{hbold('Ссылка:')} {link}"
    )
    await callback.message.edit_text(
        text,
        reply_markup=get_course_manage_kb(course_id),
        disable_web_page_preview=True,
    )
    await callback.answer()

@admin_router.callback_query(AdminCourseCallback.filter(F.action == "delete"))
async def confirm_delete_course(
    callback: CallbackQuery, callback_data: AdminCourseCallback
):
    course_id = callback_data.course_id
    await courses_db.delete_course(course_id)
    await callback.message.edit_text("Курс был успешно удален.")
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

@admin_router.callback_query(AdminCourseCallback.filter(F.action == "back_to_list"))
async def back_to_course_list_admin(callback: CallbackQuery):
    all_courses = await courses_db.get_all_courses()
    await callback.message.edit_text(
        "Выберите курс для редактирования:",
        reply_markup=get_admin_courses_kb(all_courses),
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
        "materials_link": "новую ссылку на материалы",
        "price": "новую цену",
    }
    await state.update_data(field_to_edit=field)
    await state.set_state(EditCourse.entering_new_value)
    await callback.message.delete()
    await callback.message.answer(
        f"Введите {field_names.get(field, 'новое значение')}:", reply_markup=cancel_kb
    )

@admin_router.message(EditCourse.entering_new_value)
async def process_new_value(message: Message, state: FSMContext, bot: Bot):
    new_value = message.text
    data = await state.get_data()
    course_id = data.get("course_id")
    field = data.get("field_to_edit")
    if field == "price":
        try:
            new_value = float(new_value.replace(",", "."))
        except ValueError:
            await message.answer("Неверный формат цены. Введите число (например, 1990.50).")
            return

    await courses_db.update_course_field(course_id, field, new_value)
    await state.clear()

    display_field_names = {
        "title": "Название", "short_description": "Краткое описание",
        "full_description": "Полное описание", "materials_link": "Ссылка", "price": "Цена",
    }
    display_name = display_field_names.get(field, field)
    text = f"✅ Поле {hbold(display_name)} для курса {hbold('ID ' + str(course_id))} было обновлено!"
    await message.answer(text, reply_markup=admin_main_kb)
    await view_course_after_edit(message, course_id, bot)

async def view_course_after_edit(message: Message, course_id: int, bot: Bot):
    course = await courses_db.get_course_by_id(course_id)
    if not course: return

    title = html.escape(course.get('title', ''))
    short_desc = html.escape(course.get('short_description', ''))
    full_desc = html.escape(course.get('full_description', ''))
    price = course.get('price', 0)
    link = hlink('Ссылка', course.get('materials_link', ''))

    # ИСПОЛЬЗУЕМ HTML
    text = (f"📖 {hbold('Обновленный курс')}\n\n"
            f"{hbold('ID:')} {hcode(course_id)}\n"
            f"{hbold('Название:')} {title}\n"
            f"{hbold('Краткое описание:')} {short_desc}\n"
            f"{hbold('Полное описание:')} {full_desc}\n"
            f"{hbold('Цена:')} {price} руб.\n"
            f"{hbold('Ссылка:')} {link}")

    await bot.send_message(
        chat_id=message.chat.id,
        text=text,
        reply_markup=get_course_manage_kb(course_id),
        disable_web_page_preview=True,
    )


@admin_router.message(F.text == "📊 Статистика", IsAdmin())
async def show_stats(message: Message):
    stats = await stats_db.get_main_stats()
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
            f"--------------------\n"
        )
    return text

@admin_router.message(F.text == "👥 Список юзеров", IsAdmin())
async def list_users(message: Message):
    total_users = await users_db.get_total_users_count()
    users = await users_db.get_paginated_users(limit=USERS_PER_PAGE, offset=0)
    text = await format_users_list(users)
    await message.answer(
        text,
        reply_markup=get_users_pagination_kb(
            offset=0, total_users=total_users, page_size=USERS_PER_PAGE
        ),
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
    )
    await callback.answer()
