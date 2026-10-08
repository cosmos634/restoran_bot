import asyncio
from aiogram import Bot, Dispatcher
from config import BOT_TOKEN
from handlers.commands import router as commands_router
from handlers.callbacks import router as callback_router


bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

dp.include_router(commands_router)
dp.include_router(callback_router)

async def main():
	print("Bot ishga tushdi!")
	await dp.start_polling(bot)
	

if __name__ == "__main__":
	asyncio.run(main())
