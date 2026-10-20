"""Keyboard builders. Callback payloads use ':' separators to preserve IDs with underscores."""
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from data import foods, CATEGORY_NAMES


def _button(text: str, callback_data: str) -> InlineKeyboardButton:
    return InlineKeyboardButton(text=text, callback_data=callback_data)


def main_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [_button("🍕 Меню", "menu"), _button("🛒 Корзина", "cart:show")],
        [_button("📦 Мои заказы", "orders:history")],
        [_button("☎️ Контакты", "contact")],
    ])


def categories_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for category, title in CATEGORY_NAMES.items():
        builder.button(text=title, callback_data=f"category:{category}")
    builder.button(text="⬅️ Главное меню", callback_data="home")
    builder.adjust(2, 1)
    return builder.as_markup()


def products_keyboard(category: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for product_id, product in foods.get(category, {}).items():
        builder.button(text=f"{product['name']} · {product['price']}", callback_data=f"product:{category}:{product_id}")
    builder.button(text="🛒 Корзина", callback_data="cart:show")
    builder.button(text="⬅️ Категории", callback_data="menu")
    builder.adjust(1)
    return builder.as_markup()


def product_keyboard(category: str, product_id: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="➕ Добавить в корзину", callback_data=f"cart:add:{category}:{product_id}")
    builder.button(text="⬅️ К товарам", callback_data=f"category:{category}")
    builder.button(text="🛒 Открыть корзину", callback_data="cart:show")
    builder.adjust(1)
    return builder.as_markup()


def cart_keyboard(items: list[dict]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for item in items:
        key = f"{item['category']}:{item['product_id']}"
        builder.button(text=f"➖ {item['name']}", callback_data=f"cart:adjust:-1:{key}")
        builder.button(text=f"➕ {item['name']}", callback_data=f"cart:adjust:1:{key}")
    if items:
        builder.button(text="🧹 Очистить корзину", callback_data="cart:clear")
        builder.button(text="✅ Оформить заказ", callback_data="checkout:start")
    builder.button(text="⬅️ Главное меню", callback_data="home")
    builder.adjust(2)
    return builder.as_markup()


def clear_confirmation_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[[
        _button("Да, очистить", "cart:clear:yes"),
        _button("Нет, назад", "cart:show"),
    ]])


def checkout_review_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [_button("✅ Подтвердить заказ", "checkout:confirm")],
        [_button("❌ Отменить оформление", "checkout:cancel")],
    ])


def contact_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[[
        _button("⬅️ Отменить оформление", "checkout:cancel")
    ]])


def phone_reply_keyboard():
    from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="📱 Отправить мой контакт", request_contact=True)],
                  [KeyboardButton(text="Отмена")]],
        resize_keyboard=True, one_time_keyboard=True,
    )


def remove_reply_keyboard():
    from aiogram.types import ReplyKeyboardRemove
    return ReplyKeyboardRemove()


def order_history_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[[
        _button("⬅️ Главное меню", "home")
    ]])


def admin_order_keyboard(order_number: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for status, title in [("accepted", "Принять"), ("preparing", "Готовится"),
                          ("completed", "Завершён"), ("cancelled", "Отменить")]:
        builder.button(text=title, callback_data=f"admin:status:{status}:{order_number}")
    builder.adjust(2)
    return builder.as_markup()
