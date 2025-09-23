import os
import logging
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


async def on_startup(bot: Bot, dispatcher: Dispatcher):
    pool = await create_pool()
    dispatcher.workflow_data["pool"] = pool

    await initialize_db(pool)

    await bot.set_webhook(
        TELEGRAM_WEBHOOK_URL,
        allowed_updates=["message", "callback_query", "pre_checkout_query"],
    )
    logging.info(f"Webhook set to {TELEGRAM_WEBHOOK_URL}")

async def on_shutdown(dispatcher: Dispatcher):
    logging.warning("Бот останавливается...")
    pool = dispatcher.workflow_data.get("pool")
    await close_pool(pool)
    logging.warning("Пул соединений закрыт.")


def main():
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
    )

    bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher()

    dp.message.middleware(ThrottlingMiddleware())
    dp.callback_query.middleware(ThrottlingMiddleware())

    dp.startup.register(lambda: on_startup(bot, dp))
    dp.shutdown.register(lambda: on_shutdown(dp))

    dp.include_router(user_router)
    dp.include_router(admin_router)

    app = web.Application()
    app["bot"] = bot
    app["dispatcher"] = dp

    telegram_handler = SimpleRequestHandler(dispatcher=dp, bot=bot)
    app.router.add_post(TELEGRAM_WEBHOOK_PATH, telegram_handler)

    setup_application(app, dp, bot=bot)

    logging.info("Starting web server...")
    web.run_app(app, host=APP_HOST, port=APP_PORT)


if __name__ == "__main__":
    main()
