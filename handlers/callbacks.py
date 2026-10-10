from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from buttons.inline import menu_kategorys, burger_buttons, pizza_buttons, ichimlik_butttons, create_buttons, main_menu
from data import foods
from universal_defs.defs import build_cart


router = Router()
cart = {}
user_state = "None"


def user_state_update(state):
	global user_state
	user_state = state


#===== MENU ====
@router.callback_query(F.data == "menu")
async def main_menu(callback: CallbackQuery):
	await callback.message.answer("Kategoriyani tanlang", reply_markup=menu_kategorys)
	await callback.answer()	


#===== MENU KATEGORY ====
@router.callback_query(F.data == "pizza")
async def pizza(callback: CallbackQuery):
	user_state_update(callback.data)
	await callback.message.answer("Mana bizning pitsalar", reply_markup=pizza_buttons)
	await callback.answer()
	

@router.callback_query(F.data == "burger")
async def burger(callback: CallbackQuery):
	user_state_update(callback.data)
	await callback.message.answer("Mana bizning burgerlar: ", reply_markup=burger_buttons)
	await callback.answer()


@router.callback_query(F.data == "ichimlik")
async def ichimlik(callback: CallbackQuery):
	user_state_update(callback.data)
	await callback.message.answer("Mana bizning ichimliklar", reply_markup=ichimlik_butttons)
	await callback.answer()
	

@router.callback_query(F.data == "back")
async def ortga(callback: CallbackQuery):
	await callback.message.answer("Ortga qaytish")
	await callback.answer()
	

#===== ADD TO CART =====
@router.callback_query(F.data.startswith("cart_"))
async def add_to_cart(callback: CallbackQuery):
	user_id = callback.from_user.id
	product_id = callback.data.split("_", 1)[1]
	
	if user_id not in cart:
		cart[user_id] = []
		
	cart[user_id].append((user_state, product_id))
	
	await callback.message.answer("Savatchaga qoshildi")
	await callback.answer()
	
	
#===== SHOW CART =====
@router.callback_query(F.data == "cart")
async def show_cart(callback: CallbackQuery):
	user_id = callback.from_user.id
	
	text, klaviatura = build_cart(user_id, cart)
		
	await callback.message.answer(text, reply_markup=klaviatura)
	await callback.answer()


#===== REMOVE RODUCT =====
@router.callback_query(F.data.startswith("remove_"))
async def remove_product(callback: CallbackQuery):
	user_id = callback.from_user.id
	call_split_list = callback.data.split("_", 2)
	kategory = call_split_list[1]
	product_id = call_split_list[2]
	
	if (kategory, product_id) in cart[user_id]:
		cart[user_id].remove((kategory, product_id))

	text, klaviatura = build_cart(user_id, cart)
	await callback.message.edit_text(text, reply_markup=klaviatura)
	await callback.answer()
	

#===== ADD PRODUCT =====
@router.callback_query(F.data.startswith("add_"))
async def add_product(callback: CallbackQuery):
	user_id = callback.from_user.id
	call_split_list = callback.data.split("_", 2)
	kategory = call_split_list[1]
	product_id = call_split_list[2]
	
	cart[user_id].append((kategory, product_id))
	
	text, klaviatura = build_cart(user_id, cart)
	await callback.message.edit_text(text, reply_markup=klaviatura)
	await callback.answer()
	

#===== CLEAR USER PRIDUCT =====
@router.callback_query(F.data == "clear_cart")
async def clear_cart(callback: CallbackQuery):
	user_id = callback.from_user.id
	cart[user_id].clear()
	
	await callback.message.edit_text("Savatcha tozalandi! ", reply_markup=main_menu)
	await callback.answer()


@router.callback_query()
async def food_data(callback: CallbackQuery):
	if callback.data in foods[user_state]:
		food = foods[user_state][callback.data]
		await callback.message.answer(f"{food['name']}\n\n{food['description']}\n\nNarxi: {food['price']}", reply_markup=create_buttons(callback.data))
		await callback.answer()
	else:
		await callback.message.answer("Uzur malumotlar esdan chiqgan")
		await callback.answer()
