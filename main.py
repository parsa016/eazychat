import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from config import BOT_TOKEN
from bot.database import db
from bot.handlers import registration, verification, profile_completion, search, direct_message, matches, profile, admin

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def on_startup(bot: Bot):
    await db.connect()
    logger.info("Database connected!")
    logger.info("Bot started!")


async def on_shutdown(bot: Bot):
    await db.close()
    logger.info("Database connection closed!")
    logger.info("Bot stopped!")


async def main():
    bot = Bot(token=BOT_TOKEN)
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)

    # Register routers
    dp.include_router(registration.router)
    dp.include_router(verification.router)
    dp.include_router(profile_completion.router)
    dp.include_router(search.router)
    dp.include_router(direct_message.router)
    dp.include_router(matches.router)
    dp.include_router(profile.router)
    dp.include_router(admin.router)

    # Startup/shutdown hooks
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)

    # Start polling
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
