from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message
from buttons.inline import main_menu


router = Router()


@router.message(CommandStart())
async def start(message: Message):
	await message.answer("Restoran_nomi\n\nXush kelibsiz!\nBuyurtma berish uchun menyuni tanlnag.", reply_markup=main_menu)
