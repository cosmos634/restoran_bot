from aiogram import F, Router
from aiogram.types import CallbackQuery

from buttons.inline import categories_keyboard, products_keyboard, product_keyboard, main_menu, cart_keyboard
from data import foods, get_product, CATEGORY_NAMES
from database import add_to_cart, adjust_cart, clear_cart, get_cart
from handlers.common import cart_text

router = Router()


async def safe_edit(callback: CallbackQuery, text: str, reply_markup=None) -> None:
    try:
        await callback.message.edit_text(text, reply_markup=reply_markup)
    except Exception as exc:
        # Telegram raises when content is unchanged; only then fall back to a new message.
        if "message is not modified" in str(exc).lower():
            return
        await callback.message.answer(text, reply_markup=reply_markup)


@router.callback_query(F.data == "home")
async def home(callback: CallbackQuery):
    await safe_edit(callback, "🍽 Главное меню", main_menu())
    await callback.answer()


@router.callback_query(F.data == "menu")
async def show_menu(callback: CallbackQuery):
    await safe_edit(callback, "Выберите категорию:", categories_keyboard())
    await callback.answer()


@router.callback_query(F.data.startswith("category:"))
async def show_category(callback: CallbackQuery):
    category = callback.data.split(":", 1)[1]
    if category not in foods:
        await callback.answer("Категория не найдена.", show_alert=True)
        return
    await safe_edit(callback, f"{CATEGORY_NAMES[category]} — выберите товар:", products_keyboard(category))
    await callback.answer()


@router.callback_query(F.data.startswith("product:"))
async def show_product(callback: CallbackQuery):
    parts = callback.data.split(":", 2)
    if len(parts) != 3:
        await callback.answer("Некорректная кнопка.", show_alert=True)
        return
    _, category, product_id = parts
    product = get_product(category, product_id)
    if product is None:
        await callback.answer("Товар не найден. Откройте меню заново.", show_alert=True)
        return
    text = f"🍴 {product['name']}\n\n{product['description']}\n\nЦена: {product['price']} сомони"
    await safe_edit(callback, text, product_keyboard(category, product_id))
    await callback.answer()


@router.callback_query(F.data.startswith("cart:add:"))
async def add_item(callback: CallbackQuery, database_path: str):
    parts = callback.data.split(":", 3)
    if len(parts) != 4 or not add_to_cart(callback.from_user.id, parts[2], parts[3], database_path):
        await callback.answer("Товар не найден. Откройте меню заново.", show_alert=True)
        return
    await callback.answer("Добавлено в корзину ✓")


@router.callback_query(F.data == "cart:show")
async def show_cart(callback: CallbackQuery, database_path: str, currency: str):
    items = get_cart(callback.from_user.id, database_path)
    await safe_edit(callback, cart_text(items, currency), cart_keyboard(items))
    await callback.answer()


@router.callback_query(F.data.startswith("cart:adjust:"))
async def change_item(callback: CallbackQuery, database_path: str, currency: str):
    parts = callback.data.split(":", 4)
    if len(parts) != 5:
        await callback.answer("Некорректная кнопка.", show_alert=True)
        return
    try:
        delta = int(parts[2])
    except ValueError:
        await callback.answer("Некорректное количество.", show_alert=True)
        return
    key = parts[3] + ":" + parts[4]
    category, product_id = key.split(":", 1)
    if not adjust_cart(callback.from_user.id, category, product_id, delta, database_path):
        await callback.answer("Этот товар уже отсутствует в корзине.", show_alert=True)
        return
    items = get_cart(callback.from_user.id, database_path)
    await safe_edit(callback, cart_text(items, currency), __import__("buttons.inline", fromlist=["cart_keyboard"]).cart_keyboard(items))
    await callback.answer("Корзина обновлена")


@router.callback_query(F.data == "cart:clear")
async def ask_clear(callback: CallbackQuery):
    from buttons.inline import clear_confirmation_keyboard
    await safe_edit(callback, "Очистить всю корзину?", clear_confirmation_keyboard())
    await callback.answer()


@router.callback_query(F.data == "cart:clear:yes")
async def confirm_clear(callback: CallbackQuery, database_path: str):
    clear_cart(callback.from_user.id, database_path)
    await safe_edit(callback, "Корзина очищена.", main_menu())
    await callback.answer("Корзина очищена")


@router.callback_query(F.data == "contact")
async def contact(callback: CallbackQuery):
    await safe_edit(callback, "По вопросам заказа напишите администратору ресторана. Контакт администратора можно добавить в настройках ресторана.", main_menu())
    await callback.answer()


@router.callback_query()
async def unknown_callback(callback: CallbackQuery):
    await callback.answer("Эта кнопка устарела. Откройте меню заново.", show_alert=True)
