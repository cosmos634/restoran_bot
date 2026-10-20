"""Application entry point."""
import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from config import get_settings
from database import init_db
from handlers.admin import router as admin_router
from handlers.callbacks import router as callbacks_router
from handlers.checkout import router as checkout_router
from handlers.commands import router as commands_router


async def main() -> None:
    settings = get_settings()
    init_db(settings.database_path)
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    bot = Bot(token=settings.bot_token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dispatcher = Dispatcher(storage=MemoryStorage())
    dispatcher["database_path"] = settings.database_path
    dispatcher["currency"] = settings.currency
    dispatcher["restaurant_name"] = settings.restaurant_name
    dispatcher["admin_ids"] = settings.admin_ids
    dispatcher.include_router(commands_router)
    dispatcher.include_router(callbacks_router)
    dispatcher.include_router(checkout_router)
    dispatcher.include_router(admin_router)
    try:
        await dispatcher.start_polling(bot)
    finally:
        await bot.session.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except ValueError as exc:
        raise SystemExit(str(exc)) from exc
