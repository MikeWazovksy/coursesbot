from aiogram.types import (
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.filters.callback_data import CallbackData

admin_main_kb = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="➕ Добавить курс"),
            KeyboardButton(text="📋 Список курсов"),
        ],
        [KeyboardButton(text="👥 Список юзеров"), KeyboardButton(text="📊 Статистика")],
        [KeyboardButton(text="✏️ Изменить приветствие")],
    ],
    resize_keyboard=True,
)


cancel_kb = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text="❌ Отмена")]], resize_keyboard=True
)

class AdminCourseCallback(CallbackData, prefix="admin_course"):
    action: str
    course_id: int


class AdminCoursePaginationCallback(CallbackData, prefix="admin_course_page"):
    action: str
    offset: int


def get_admin_courses_kb(courses: list, offset: int, total_courses: int, page_size: int):
    builder = InlineKeyboardBuilder()
    for course in courses:
        builder.button(
            text=f"ID: {course[0]} | {course[1]}",
            callback_data=AdminCourseCallback(action="view", course_id=course[0]),
        )

    pagination_buttons = []
    if offset > 0:
        pagination_buttons.append(
            InlineKeyboardButton(
                text="⬅️ Назад",
                callback_data=AdminCoursePaginationCallback(action="prev", offset=offset).pack(),
            )
        )
    if offset + page_size < total_courses:
        pagination_buttons.append(
            InlineKeyboardButton(
                text="Вперёд ➡️",
                callback_data=AdminCoursePaginationCallback(action="next", offset=offset).pack(),
            )
        )

    builder.row(*pagination_buttons)

    builder.button(
        text="⬅️ Назад в меню",
        callback_data=AdminCourseCallback(action="back_to_main_menu", course_id=0),
    )

    builder.adjust(1)
    return builder.as_markup()


def get_course_manage_kb(course_id: int):
    """Генерирует меню управления для выбранного курса."""
    builder = InlineKeyboardBuilder()
    builder.button(
        text="✏️ Редактировать",
        callback_data=AdminCourseCallback(action="edit", course_id=course_id),
    )
    builder.button(
        text="🗑️ Удалить",
        callback_data=AdminCourseCallback(action="delete", course_id=course_id),
    )
    builder.button(
        text="⬅️ Назад к списку",
        callback_data=AdminCourseCallback(action="back_to_list", course_id=0),
    )
    builder.adjust(2, 1)
    return builder.as_markup()

def get_confirm_delete_kb(course_id: int):
    """Генерирует клавиатуру для подтверждения удаления курса."""
    builder = InlineKeyboardBuilder()
    builder.button(
        text="✅ Да, удалить",
        callback_data=AdminCourseCallback(action="confirm_delete", course_id=course_id),
    )
    builder.button(
        text="❌ Нет, отмена",
        callback_data=AdminCourseCallback(action="view", course_id=course_id),
    )
    builder.adjust(2)
    return builder.as_markup()


class EditCourseCallback(CallbackData, prefix="edit_course_field"):
    course_id: int
    field: str


def get_edit_field_kb(course_id: int):
    builder = InlineKeyboardBuilder()
    fields = {
        "title": "Название",
        "short_description": "Краткое описание",
        "full_description": "Полное описание",
        "materials_link": "Ссылка на материалы",
        "price": "Цена",
    }
    for field, name in fields.items():
        builder.button(
            text=name,
            callback_data=EditCourseCallback(course_id=course_id, field=field),
        )
    builder.button(
        text="⬅️ Назад",
        callback_data=AdminCourseCallback(action="view", course_id=course_id),
    )
    builder.adjust(2, 2, 1)
    return builder.as_markup()

class UserPaginationCallback(CallbackData, prefix="users_page"):
    action: str
    offset: int


def get_users_pagination_kb(
    offset: int, total_users: int, page_size: int
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    if offset > 0:
        builder.button(
            text="⬅️ Назад",
            callback_data=UserPaginationCallback(action="prev", offset=offset),
        )
    if offset + page_size < total_users:
        builder.button(
            text="Вперёд ➡️",
            callback_data=UserPaginationCallback(action="next", offset=offset),
        )

    return builder.as_markup()
