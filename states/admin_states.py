from aiogram.fsm.state import State, StatesGroup

class AddCourse(StatesGroup):

    title = State()  # Ввод названия
    short_description = State()  # Крипткое описание
    full_description = State()  # Полное описание
    materials_link = State()  # Ссылка на курс
    price = State()  # Ввод цены

class EditCourse(StatesGroup):
    """Состояния для редактирования курса."""

    choosing_field = State()  # Ожидаем выбор поля
    entering_new_value = State()  # Ожидаем новое значение
