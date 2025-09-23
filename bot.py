# bot.py (исправленная версия)
import os
import logging
import asyncio
from aiogram.enums import ParseMode
from aiohttp import web
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application

from config import BOT_TOKEN, WEBHOOK_HOST
from database import initialize_db, create_pool, close_pool

from handlers.user import user_router
from handlers.admin import admin_router
from middlewares.throttling import ThrottlingMiddleware

TELEGRAM_WEBHOOK_PATH = "/webhook"
WEBHOOK_HOST = os.getenv("WEBHOOK_HOST", "").rstrip('/')
TELEGRAM_WEBHOOK_URL = f"{WEBHOOK_HOST}{TELEGRAM_WEBHOOK_PATH}"
APP_HOST = "0.0.0.0"
APP_PORT = int(os.environ.get("PORT", 8080))


async def on_startup(app: web.Application):
    """Действия при запуске приложения."""
    bot: Bot = app["bot"]
    pool = app["pool"]

    await initialize_db(pool)

    await bot.set_webhook(
        TELEGRAM_WEBHOOK_URL,
        allowed_updates=["message", "callback_query", "pre_checkout_query"],
    )
    logging.info(f"Webhook set to {TELEGRAM_WEBHOOK_URL}")


async def on_shutdown(app: web.Application):
    """Действия при остановке приложения."""
    logging.warning("Бот останавливается...")
    pool = app["pool"]
    await close_pool(pool)
    logging.warning("Пул соединений закрыт.")


async def main():
    """Основная функция для запуска бота."""
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
    )

    bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher()

    pool = await create_pool()

    dp.message.middleware(ThrottlingMiddleware())
    dp.callback_query.middleware(ThrottlingMiddleware())
    dp.include_router(user_router)
    dp.include_router(admin_router)

    app = web.Application()

    app["bot"] = bot
    app["pool"] = pool

    telegram_handler = SimpleRequestHandler(
        dispatcher=dp,
        bot=bot,
        pool=pool
    )

    app.router.add_post(TELEGRAM_WEBHOOK_PATH, telegram_handler)

    app.on_startup.append(on_startup)
    app.on_shutdown.append(on_shutdown)

    logging.info("Starting web server...")
    web.run_app(app, host=APP_HOST, port=APP_PORT)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.info("Bot stopped!")
