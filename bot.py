import os
import logging
import asyncio
from aiogram.enums import ParseMode
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiohttp import web

from config import BOT_TOKEN
from database import initialize_db, create_pool, close_pool
from handlers.user import user_router
from handlers.admin import admin_router
from middlewares.throttling import ThrottlingMiddleware

APP_HOST = "0.0.0.0"
APP_PORT = int(os.environ.get("PORT", 8080))


# =======================
# Фиктивный HTTP-сервер для Render , чтоб слушал порт
# =======================
async def handle(request):
    return web.Response(text="Bot is running!")

async def start_dummy_server():
    app = web.Application()
    app.add_routes([web.get("/", handle)])
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, APP_HOST, APP_PORT)
    await site.start()
    logging.info(f"Dummy HTTP server running on {APP_HOST}:{APP_PORT}")


# =======================
# Основной код бота
# =======================
async def main():
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
    )

    # Запуск фиктивного HTTP-сервера чисто для Render.com
    asyncio.create_task(start_dummy_server())

    bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    await bot.delete_webhook(drop_pending_updates=True)

    dp = Dispatcher()

    # Создаем и инициализируем пул соединений с БД
    pool = await create_pool()
    await initialize_db(pool)

    dp.message.middleware(ThrottlingMiddleware())
    dp.callback_query.middleware(ThrottlingMiddleware())
    dp.include_router(user_router)
    dp.include_router(admin_router)

    # Запускаем long polling
    try:
        logging.info("Бот запускается в режиме long polling...")
        await dp.start_polling(bot, pool=pool)
    finally:
        await close_pool(pool)
        logging.warning("Пул соединений закрыт.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.info("Бот остановлен!")
