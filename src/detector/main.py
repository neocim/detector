import asyncio
import logging

from aiogram import Bot, Dispatcher

from detector.config import load_config
from detector.di import get_async_container, setup_di
from detector.telegram_bot.handlers.photo import photo_router
from detector.telegram_bot.handlers.start import start_router

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


async def async_main() -> None:
    config = load_config("config.toml")
    container = get_async_container(config)
    bot = Bot(config.telegram_bot.token)

    dispatcher = Dispatcher()
    dispatcher.include_router(start_router)
    dispatcher.include_router(photo_router)
    setup_di(container, dispatcher, auto_inject=True)

    logger.info("Bot start polling!")
    await dispatcher.start_polling(bot)


def main() -> None:
    asyncio.run(async_main())
