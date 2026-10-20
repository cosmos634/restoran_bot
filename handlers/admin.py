"""Telegram admin commands and inline order management."""
from html import escape

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

from database import get_order_by_number, get_order_items, list_orders, order_stats, update_order_status

router = Router()

STATUS_NAMES = {
    "pending": "Ожидает",
    "accepted": "Принят",
    "preparing": "Готовится",
    "completed": "Завершён",
    "cancelled": "Отменён",
}
STATUS_BUTTONS = [
    ("accepted", "✅ Принять"),
    ("preparing", "👨‍🍳 Готовится"),
    ("completed", "🏁 Завершён"),
    ("cancelled", "❌ Отменить"),
]


def is_admin(user_id: int, admin_ids: frozenset[int] | set[int]) -> bool:
    return user_id in admin_ids


def panel_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📦 Последние заказы", callback_data="admin:orders")],
        [InlineKeyboardButton(text="📊 Статистика", callback_data="admin:stats")],
        [InlineKeyboardButton(text="🔄 Обновить", callback_data="admin:home")],
    ])


def order_list_keyboard(orders: list[dict]) -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(
            text=f"{order['order_number']} · {order['total']} · {STATUS_NAMES.get(order['status'], order['status'])}",
            callback_data=f"admin:order:{order['order_number']}",
        )]
        for order in orders
    ]
    rows.append([InlineKeyboardButton(text="⬅️ Админ-панель", callback_data="admin:home")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def order_keyboard(order_number: str) -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(text=label, callback_data=f"admin:status:{status}:{order_number}")]
        for status, label in STATUS_BUTTONS
    ]
    rows.append([InlineKeyboardButton(text="⬅️ Заказы", callback_data="admin:orders")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def format_order(order: dict, items: list[dict], currency: str) -> str:
    fulfillment = "Доставка" if order["fulfillment"] == "delivery" else "Самовывоз"
    lines = [
        f"📦 <b>Заказ {escape(str(order['order_number']))}</b>",
        f"Статус: <b>{escape(STATUS_NAMES.get(order['status'], str(order['status'])))}</b>",
        f"Имя: {escape(str(order['customer_name']))}",
        f"Телефон: {escape(str(order['phone']))}",
        f"Telegram ID: <code>{order['user_id']}</code>",
        f"Получение: {fulfillment}",
    ]
    if order.get("address"):
        lines.append(f"Адрес: {escape(str(order['address']))}")
    lines.append("\n<b>Состав заказа:</b>")
    lines.extend(
        f"• {escape(str(item['product_name']))} × {item['quantity']} — {item['line_total']} {escape(currency)}"
        for item in items
    )
    lines.append(f"\nИтого: <b>{order['total']} {escape(currency)}</b>")
    lines.append(f"Создан: {escape(str(order['created_at']))}")
    return "\n".join(lines)


@router.message(Command("admin"))
async def admin_panel(message: Message, admin_ids: frozenset[int], database_path: str):
    if not is_admin(message.from_user.id, admin_ids):
        await message.answer("⛔ Нет доступа.")
        return
    stats = order_stats(database_path)
    await message.answer(
        "🛠 <b>Панель администратора</b>\n\n"
        f"Всего заказов: {stats['total']}\n"
        f"Ожидают: {stats['pending']}\n"
        f"Выручка (без отменённых): {stats['revenue']}",
        reply_markup=panel_keyboard(),
    )


@router.callback_query(F.data.startswith("admin:"))
async def admin_actions(callback: CallbackQuery, database_path: str, admin_ids: frozenset[int], currency: str):
    if not is_admin(callback.from_user.id, admin_ids):
        await callback.answer("Нет доступа.", show_alert=True)
        return
    data = callback.data or ""

    if data in {"admin:home", "admin:orders", "admin:stats"}:
        if data == "admin:orders":
            orders = list_orders(database_path, 15)
            text = "📦 <b>Последние заказы</b>"
            if not orders:
                text += "\nЗаказов пока нет."
                markup = InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="⬅️ Админ-панель", callback_data="admin:home")]
                ])
            else:
                markup = order_list_keyboard(orders)
        elif data == "admin:stats":
            stats = order_stats(database_path)
            text = (
                "📊 <b>Статистика заказов</b>\n\n"
                f"Всего: {stats['total']}\n"
                f"Ожидают: {stats['pending']}\n"
                f"Приняты: {stats['accepted']}\n"
                f"Готовятся: {stats['preparing']}\n"
                f"Завершены: {stats['completed']}\n"
                f"Отменены: {stats['cancelled']}\n"
                f"Сумма заказов без отменённых: <b>{stats['revenue']} {escape(currency)}</b>"
            )
            markup = panel_keyboard()
        else:
            stats = order_stats(database_path)
            text = (
                "🛠 <b>Панель администратора</b>\n\n"
                f"Всего заказов: {stats['total']}\n"
                f"Ожидают: {stats['pending']}\n"
                f"Выручка (без отменённых): {stats['revenue']} {escape(currency)}"
            )
            markup = panel_keyboard()
        try:
            await callback.message.edit_text(text, reply_markup=markup)
        except Exception:
            pass
        await callback.answer()
        return

    if data.startswith("admin:order:"):
        order_number = data.split(":", 2)[2]
        order = get_order_by_number(order_number, database_path)
        if not order:
            await callback.answer("Заказ не найден.", show_alert=True)
            return
        text = format_order(order, get_order_items(order["id"], database_path), currency)
        try:
            await callback.message.edit_text(text, reply_markup=order_keyboard(order_number))
        except Exception:
            pass
        await callback.answer()
        return

    if data.startswith("admin:status:"):
        parts = data.split(":", 3)
        if len(parts) != 4:
            await callback.answer("Некорректная команда.", show_alert=True)
            return
        _, _, status, order_number = parts
        if status not in STATUS_NAMES or not update_order_status(order_number, status, database_path):
            await callback.answer("Заказ не найден или статус недопустим.", show_alert=True)
            return
        order = get_order_by_number(order_number, database_path)
        text = format_order(order, get_order_items(order["id"], database_path), currency)
        try:
            await callback.message.edit_text(text, reply_markup=order_keyboard(order_number))
        except Exception:
            pass
        await callback.answer("Статус обновлён")
