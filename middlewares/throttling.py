# middlewares/throttling.py

from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import Message
from cachetools import TTLCache


class ThrottlingMiddleware(BaseMiddleware):

    def __init__(self, time_limit: int = 1):
        # Лимит на запросы к боту , чтоб не спамить его
        self.cache = TTLCache(maxsize=10_000, ttl=time_limit)

    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: Dict[str, Any],
    ) -> Any:
        if event.chat.id in self.cache:
            return

        self.cache[event.chat.id] = None

        return await handler(event, data)
