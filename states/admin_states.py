from aiogram.fsm.state import State, StatesGroup

class AddCourse(StatesGroup):

    title = State()
    short_description = State()
    full_description = State()
    materials_link = State()
    price = State()


class EditCourse(StatesGroup):

    choosing_field = State()
    entering_new_value = State()

class EditWelcomeMessage(StatesGroup):
    entering_message = State()
