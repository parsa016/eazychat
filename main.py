import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.client.session.aiohttp import AiohttpSession

from config import BOT_TOKEN, PROXY_URL
from bot.database import db
from bot.handlers import registration, verification, profile_completion, search, matches, profile, admin, referral

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def on_startup(bot: Bot):
    await db.connect()
    logger.info("Database connected!")
    logger.info("Bot started!")

    # Broadcast to all users that bot is online
    try:
        users = await db.fetchall("SELECT id FROM users WHERE is_active = 1")
        sent = 0
        for user in users:
            try:
                await bot.send_message(user['id'], "🟢 ربات در دسترس قرار گرفت!")
                sent += 1
            except Exception:
                pass
        logger.info(f"Startup broadcast sent to {sent} users")
    except Exception as e:
        logger.error(f"Startup broadcast failed: {e}")


async def on_shutdown(bot: Bot):
    await db.close()
    logger.info("Database connection closed!")
    logger.info("Bot stopped!")


async def main():
    # Setup proxy if configured
    session = None
    if PROXY_URL:
        session = AiohttpSession(proxy=PROXY_URL)
        logger.info(f"Using proxy: {PROXY_URL}")

    bot = Bot(token=BOT_TOKEN, session=session)
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)

    # Register routers (verification first to catch video notes in verification state)
    dp.include_router(verification.router)
    dp.include_router(registration.router)
    dp.include_router(profile_completion.router)
    dp.include_router(search.router)
    dp.include_router(matches.router)
    dp.include_router(profile.router)
    dp.include_router(referral.router)
    dp.include_router(admin.router)

    # Startup/shutdown hooks
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)

    # Start polling
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
