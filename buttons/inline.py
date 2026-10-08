from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


#===== MENU ITEMS =====
menus = [
	{
		"name": "Pitsalar",
		"cal_data": "pizza"
	},
	{
		"name": "Burgerlar",
		"cal_data": "burger"
	},
	{
		"name": "Ichimliklar",
		"cal_data": "ichimlik"
	},
	{
		"name": "Orqaga",
		"cal_data": "back"
	}
]


#===== BURGERS DATA =====
burgers = [
	{
		"name": "Cheeseburger",
		"cal_data": "cheesburger"
	},
	{
		"name": "Chicken Burger",
		"cal_data": "chicken_burger"
	},
	{
		"name": "Double Burger",
		"cal_data": "double_burger"
	},
	{
		"name": "Orqaga",
		"cal_data": "back"
	}
]


#===== PIZZA DATA
pizzas = [
	{
		"name": "Margarita",
		"cal_data": "margarita"
	},
	{
		"name": "Pepperoni",
		"cal_data": "pepperoni"
	},
	{
		"name": "Chicken",
		"cal_data": "chiken"
	},
	{
		"name": "Cheese",
		"cal_data": "cheese"
	},
	{
		"name": "Meat pizza",
		"cal_data": "meat_pizza"
	},
	{
		"name": "Orqaga",
		"cal_data": "back"
	}
]


#===== ISHIMLIKLAR DATA =====
ichimliklar = [
	{
		"name": "Coca-Cola",
		"cal_data": "coca_cola"
	},
	{
		"name": "Fanta",
		"cal_data": "fanta"
	},
	{
		"name": "Sprite",
		"cal_data": "sprite"
	},
	{
		"name": "Apelsin sharbati",
		"cal_data": "apelsin_sharbat"
	},
	{
		"name": "Olam sharbati",
		"cal_data": "olma_sharbat"
	},
	{
		"name": "Orqaga",
		"cal_data": "back"
	}
]


#====== MAIN MENU =====
main_menu = InlineKeyboardMarkup(
	inline_keyboard=[
		[
			InlineKeyboardButton(text="Menyu", callback_data="menu"),
			InlineKeyboardButton(text="Savatcha", callback_data="cart")
		],
		[InlineKeyboardButton(text="Mening Buyurtmalarim", callback_data="mening_buyurtmalarim")],
		[InlineKeyboardButton(text="Aloqa", callback_data="aloqa")]
	]
)


#====== MENYU KATEGORY ======
builder = InlineKeyboardBuilder()
for menu in menus:
	builder.button(text=menu["name"], callback_data=menu["cal_data"])
	
builder.adjust(2)

menu_kategorys = builder.as_markup()


#===== BURGER KATEGORY =====
burger_builder = InlineKeyboardBuilder()
for burger in burgers:
	burger_builder.button(text=burger["name"], callback_data=burger["cal_data"])
	
burger_builder.adjust(1)
burger_buttons = burger_builder.as_markup()


#===== PIZZA KATEGORY =====
pizza_builder = InlineKeyboardBuilder()
for pizza in pizzas:
	pizza_builder.button(text=pizza["name"], callback_data=pizza["cal_data"])
	
pizza_builder.adjust(2)
pizza_buttons = pizza_builder.as_markup()


#===== ICHIMLIK KATEGORY
ichimlik_builder = InlineKeyboardBuilder()
for ichimlik in ichimliklar:
	ichimlik_builder.button(text=ichimlik["name"], callback_data=ichimlik["cal_data"])

ichimlik_builder.adjust(2)
ichimlik_butttons = ichimlik_builder.as_markup()


#===== BUYURTMA TUGMASI =====
def create_buttons(call_data):
	button_builder = InlineKeyboardBuilder()
	button_builder.button(text="Savatchaga", callback_data=f"cart_{call_data}")
	button_builder.button(text="Orqaga", callback_data="back")
	
	button_builder.adjust(2)
	buyurtma_tugmasi = button_builder.as_markup()
	
	return buyurtma_tugmasi


#===== SAVATCHA TUGMALAR =====
def cart_product_buttons(category, product_id):
	cart_button_builder = InlineKeyboardBuilder()
	
	cart_button_builder.button(text="-", callback_data=f"remove_{category}_product_id")
	cart_button_builder.button(text="+", callback_data=f"add_{category}_product_id")
	cart_button_builder.adjuts(2)
	cart_button = cart_button_builder.as_markup()
	
	return cart_button
