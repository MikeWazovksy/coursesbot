from aiogram.types import (
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.filters.callback_data import CallbackData

# ------------------------------------------------------------------------------------
# Клавиатура админа
admin_main_kb = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="➕ Добавить курс"),
            KeyboardButton(text="📋 Список курсов"),
        ],
        [KeyboardButton(text="👥 Список юзеров"), KeyboardButton(text="📊 Статистика")],
    ],
    resize_keyboard=True,
)


# ------------------------------------------------------------------------------------
# Клавиатура отмены действий
cancel_kb = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text="❌ Отмена")]], resize_keyboard=True
)


# ------------------------------------------------------------------------------------
# Колбэк курсов
class AdminCourseCallback(CallbackData, prefix="admin_course"):
    action: str
    course_id: int


# ------------------------------------------------------------------------------------
# Вернуться в меню
def get_admin_courses_kb(courses: list):
    builder = InlineKeyboardBuilder()
    for course in courses:
        builder.button(
            text=f"ID: {course[0]} | {course[1]}",
            callback_data=AdminCourseCallback(action="view", course_id=course[0]),
        )

    builder.button(
        text="⬅️ Назад в меню",
        callback_data=AdminCourseCallback(action="back_to_main_menu", course_id=0),
    )

    builder.adjust(1)
    return builder.as_markup()


# ------------------------------------------------------------------------------------
# Кнопки редактирования и возврата назад к списку курсов
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


# ------------------------------------------------------------------------------------
# Колбэк юзеров
class EditCourseCallback(CallbackData, prefix="edit_course_field"):
    course_id: int
    field: str


# ------------------------------------------------------------------------------------
# Клавитаура выбора поля
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
    # Кнопка назад
    builder.button(
        text="⬅️ Назад",
        callback_data=AdminCourseCallback(action="view", course_id=course_id),
    )
    builder.adjust(2, 2, 1)
    return builder.as_markup()


# ------------------------------------------------------------------------------------
# Страница пользователей
class UserPaginationCallback(CallbackData, prefix="users_page"):
    action: str
    offset: int


# ------------------------------------------------------------------------------------
# Клавиатура для пагинации
def get_users_pagination_kb(
    offset: int, total_users: int, page_size: int
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    # Кнопка "Назад"
    if offset > 0:
        builder.button(
            text="⬅️ Назад",
            callback_data=UserPaginationCallback(action="prev", offset=offset),
        )

    # Кнопка "Вперёд"
    if offset + page_size < total_users:
        builder.button(
            text="Вперёд ➡️",
            callback_data=UserPaginationCallback(action="next", offset=offset),
        )

    return builder.as_markup()
