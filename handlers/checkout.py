from __future__ import annotations

import html
import uuid
from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.filters import StateFilter
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message

from buttons.inline import checkout_review_keyboard, main_menu, phone_reply_keyboard, remove_reply_keyboard
from database import create_order, get_cart, get_order_items, order_history
from handlers.common import cart_text

router = Router()


class Checkout(StatesGroup):
    name = State()
    phone = State()
    fulfillment = State()
    address = State()
    review = State()


@router.message(StateFilter(Checkout.name, Checkout.phone, Checkout.fulfillment, Checkout.address, Checkout.review), F.text.lower() == "отмена")
async def cancel_checkout_any_step(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Оформление отменено. Корзина сохранена.", reply_markup=main_menu())


def _review_text(data: dict, items: list[dict], currency: str) -> str:
    fulfillment = "Доставка" if data["fulfillment"] == "delivery" else "Самовывоз"
    address = f"\nАдрес: {html.escape(data['address'])}" if data["fulfillment"] == "delivery" else ""
    safe_items = [dict(item, name=html.escape(item["name"])) for item in items]
    return (
        "📋 <b>Проверьте заказ</b>\n\n"
        f"Имя: {html.escape(data['customer_name'])}\nТелефон: {html.escape(data['phone'])}\n"
        f"Получение: {fulfillment}{address}\n\n"
        f"{cart_text(safe_items, currency)}\n\n"
        "Оплата: наличными при получении. Онлайн-оплата не подключена."
    )


@router.callback_query(F.data == "checkout:start")
async def checkout_start(callback: CallbackQuery, state: FSMContext, database_path: str):
    if not get_cart(callback.from_user.id, database_path):
        await callback.answer("Сначала добавьте товары в корзину.", show_alert=True)
        return
    await state.clear()
    await state.update_data(confirmation_token=uuid.uuid4().hex)
    await state.set_state(Checkout.name)
    await callback.message.answer("Как вас зовут? Введите имя (2–60 символов).")
    await callback.answer()


@router.message(Checkout.name)
async def checkout_name(message: Message, state: FSMContext):
    name = (message.text or "").strip()
    if not 2 <= len(name) <= 60:
        await message.answer("Имя должно содержать от 2 до 60 символов. Попробуйте ещё раз.")
        return
    await state.update_data(customer_name=name)
    await state.set_state(Checkout.phone)
    await message.answer("Введите номер телефона или нажмите кнопку, чтобы отправить контакт.", reply_markup=phone_reply_keyboard())


async def _save_phone_and_ask_method(message: Message, state: FSMContext, phone: str):
    await state.update_data(phone=phone)
    await state.set_state(Checkout.fulfillment)
    await message.answer("Как получите заказ? Напишите «Доставка» или «Самовывоз». Для отмены напишите «Отмена».", reply_markup=remove_reply_keyboard())


@router.message(Checkout.phone, F.contact)
async def checkout_contact(message: Message, state: FSMContext):
    if message.contact.user_id not in (None, message.from_user.id):
        await message.answer("Пожалуйста, отправьте свой собственный контакт.")
        return
    phone = (message.contact.phone_number or "").strip()
    if sum(char.isdigit() for char in phone) < 7:
        await message.answer("Номер телефона выглядит некорректно. Введите его текстом.")
        return
    await _save_phone_and_ask_method(message, state, phone)


@router.message(Checkout.phone)
async def checkout_phone(message: Message, state: FSMContext):
    phone = (message.text or "").strip()
    if sum(char.isdigit() for char in phone) < 7 or len(phone) > 25:
        await message.answer("Введите корректный номер телефона (не менее 7 цифр).")
        return
    await _save_phone_and_ask_method(message, state, phone)


@router.message(Checkout.fulfillment)
async def checkout_fulfillment(message: Message, state: FSMContext, database_path: str, currency: str):
    answer = (message.text or "").strip().casefold()
    if answer in {"отмена", "cancel"}:
        await state.clear()
        await message.answer("Оформление отменено. Корзина сохранена.", reply_markup=main_menu())
    elif answer in {"доставка", "delivery"}:
        await state.update_data(fulfillment="delivery")
        await state.set_state(Checkout.address)
        await message.answer("Введите адрес доставки (5–200 символов).")
    elif answer in {"самовывоз", "заберу сам", "pickup"}:
        await state.update_data(fulfillment="pickup", address="")
        await show_review(message, state, database_path, currency)
    else:
        await message.answer("Напишите «Доставка» или «Самовывоз». Для отмены напишите «Отмена».")


@router.message(Checkout.address)
async def checkout_address(message: Message, state: FSMContext, database_path: str, currency: str):
    address = (message.text or "").strip()
    if not 5 <= len(address) <= 200:
        await message.answer("Адрес должен содержать от 5 до 200 символов.")
        return
    await state.update_data(address=address)
    await show_review(message, state, database_path, currency)


async def show_review(message: Message, state: FSMContext, database_path: str, currency: str):
    data = await state.get_data()
    items = get_cart(message.from_user.id, database_path)
    if not items:
        await state.clear()
        await message.answer("Корзина пуста. Оформление отменено.", reply_markup=main_menu())
        return
    await state.set_state(Checkout.review)
    await message.answer(_review_text(data, items, currency), reply_markup=checkout_review_keyboard(), parse_mode="HTML")


@router.callback_query(F.data == "checkout:cancel")
async def cancel_checkout(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.answer("Оформление отменено. Корзина сохранена.", reply_markup=main_menu())
    await callback.answer("Оформление отменено")


@router.callback_query(F.data == "checkout:confirm")
async def confirm_checkout(callback: CallbackQuery, state: FSMContext, database_path: str, currency: str, admin_ids: frozenset[int], bot):
    data = await state.get_data()
    if not data.get("confirmation_token") or not data.get("customer_name") or not data.get("phone") or not data.get("fulfillment"):
        await callback.answer("Сессия оформления истекла. Начните заново.", show_alert=True)
        return
    try:
        order = create_order(
            user_id=callback.from_user.id, customer_name=data["customer_name"], phone=data["phone"],
            fulfillment=data["fulfillment"], address=data.get("address", ""),
            confirmation_token=data["confirmation_token"], db_path=database_path,
        )
    except ValueError:
        await callback.answer("Проверьте данные заказа и попробуйте снова.", show_alert=True)
        return
    if order is None:
        await state.clear()
        await callback.message.answer("Корзина пуста. Добавьте товары и оформите заказ заново.", reply_markup=main_menu())
        await callback.answer()
        return
    items = get_order_items(order["id"], database_path)
    await state.clear()
    await callback.message.answer(
        f"✅ <b>Заказ принят!</b>\nНомер заказа: <code>{order['order_number']}</code>\n"
        f"Сумма: {order['total']} {html.escape(currency)}\nОплата: наличными при получении.",
        reply_markup=main_menu(), parse_mode="HTML",
    )
    await callback.answer("Заказ сохранён")
    if admin_ids:
        item_lines = "\n".join(f"• {html.escape(item['product_name'])} × {item['quantity']} — {item['line_total']} {html.escape(currency)}" for item in items)
        method = "Доставка" if order["fulfillment"] == "delivery" else "Самовывоз"
        admin_text = (
            f"🆕 <b>Новый заказ {html.escape(order['order_number'])}</b>\n"
            f"Клиент: {html.escape(order['customer_name'])}\nТелефон: {html.escape(order['phone'])}\n"
            f"Telegram ID: {order['user_id']}\nПолучение: {method}\n"
            f"Адрес: {html.escape(order['address'] or '—')}\n\n{item_lines}\n\n"
            f"Итого: {order['total']} {html.escape(currency)}\nСтатус: {order['status']}"
        )
        from buttons.inline import admin_order_keyboard
        for admin_id in admin_ids:
            try:
                await bot.send_message(admin_id, admin_text, reply_markup=admin_order_keyboard(order["order_number"]), parse_mode="HTML")
            except Exception:
                # An unreachable admin must not undo a committed customer order.
                pass


@router.callback_query(F.data == "orders:history")
async def show_history(callback: CallbackQuery, database_path: str, currency: str):
    orders = order_history(callback.from_user.id, database_path)
    if not orders:
        text = "📦 У вас пока нет заказов."
    else:
        lines = ["📦 <b>Ваши заказы</b>", ""]
        for order in orders[:10]:
            date = order["created_at"].replace("T", " ")[:16]
            lines.append(f"• <code>{html.escape(order['order_number'])}</code> — {order['total']} {html.escape(currency)} — {html.escape(order['status'])} — {date}")
        text = "\n".join(lines)
    await callback.message.answer(text, reply_markup=main_menu(), parse_mode="HTML")
    await callback.answer()
