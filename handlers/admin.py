from aiogram import F, Router
from aiogram.types import CallbackQuery
from database import get_order_by_number, update_order_status

router = Router()
STATUS_NAMES = {"pending": "Ожидает", "accepted": "Принят", "preparing": "Готовится", "completed": "Завершён", "cancelled": "Отменён"}


def is_admin(user_id: int, admin_ids: frozenset[int] | set[int]) -> bool:
    return user_id in admin_ids


@router.callback_query(F.data.startswith("admin:status:"))
async def set_status(callback: CallbackQuery, database_path: str, admin_ids: frozenset[int], currency: str):
    if not is_admin(callback.from_user.id, admin_ids):
        await callback.answer("Нет доступа.", show_alert=True)
        return
    parts = callback.data.split(":", 3)
    if len(parts) != 4:
        await callback.answer("Некорректная команда.", show_alert=True)
        return
    _, _, status, order_number = parts
    if status not in STATUS_NAMES or not update_order_status(order_number, status, database_path):
        await callback.answer("Заказ не найден или статус недопустим.", show_alert=True)
        return
    order = get_order_by_number(order_number, database_path)
    try:
        await callback.message.edit_text(
            f"Заказ <code>{order_number}</code> обновлён.\nСтатус: <b>{STATUS_NAMES[status]}</b>\nСумма: {order['total']} {currency}",
            parse_mode="HTML",
        )
    except Exception:
        pass
    await callback.answer("Статус обновлён")
