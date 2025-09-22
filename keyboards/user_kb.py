from aiogram.types import (
    ReplyKeyboardMarkup,
    KeyboardButton,
)
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.filters.callback_data import CallbackData

# Главное меню
main_menu_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🎓 Доступные курсы")],
        [
            KeyboardButton(text="📚 Мои курсы"),
            KeyboardButton(text="🧾 История покупок"),
        ],
    ],
    resize_keyboard=True,
)


# Колбэки курсов
class CourseCallbackFactory(CallbackData, prefix="course"):
    action: str
    course_id: int


# Клавиатуры для курсов
def get_courses_list_kb(courses: list):
    builder = InlineKeyboardBuilder()
    for course_id, title, _, _, price, _ in courses:
        builder.button(
            text=f"{title} - {price} руб.",
            callback_data=CourseCallbackFactory(action="view", course_id=course_id),
        )
    builder.adjust(1)
    return builder.as_markup()


def get_course_details_kb(course_id: int):
    builder = InlineKeyboardBuilder()
    builder.button(
        text="💳 Купить курс",
        callback_data=CourseCallbackFactory(action="buy", course_id=course_id),
    )
    builder.button(
        text="⬅️ Назад к списку",
        callback_data=CourseCallbackFactory(
            action="back_to_list", course_id=-1
        ),
    )
    builder.adjust(1)
    return builder.as_markup()
