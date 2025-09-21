# filters/admin.py

from aiogram.filters import BaseFilter
from aiogram.types import Message
from typing import Union

from config import ADMIN_IDS


class IsAdmin(BaseFilter):

    async def __call__(self, message: Message) -> bool:
        return message.from_user.id in ADMIN_IDS
