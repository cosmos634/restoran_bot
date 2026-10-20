from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message
from buttons.inline import main_menu

router = Router()


@router.message(CommandStart())
async def start(message: Message, restaurant_name: str):
    await message.answer(
        f"🍽 Добро пожаловать в {restaurant_name}!\n\nВыберите действие в меню ниже.",
        reply_markup=main_menu(),
    )
