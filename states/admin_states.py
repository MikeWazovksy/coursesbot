from aiogram.fsm.state import State, StatesGroup

class AddCourse(StatesGroup):

    title = State()  # Ввод названия
    short_description = State()  # Краткое описнаие курса
    full_description = State()  # Полное описание курса
    materials_link = State()  # Ссылка на курс
    price = State()  # Ввод цены


class EditCourse(StatesGroup):

    choosing_field = State()  # Ожидание выбора поля
    entering_new_value = State()  # Ожидание нового значения
