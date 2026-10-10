from aiogram.utils.keyboard import InlineKeyboardBuilder
from buttons.inline import main_menu
from data import foods

def build_cart(user_id, cart):
	text = ""
	counts = {}
	total = 0
	i = 0
	keyboard = InlineKeyboardBuilder()
	
	if user_id not in cart or not cart[user_id]:
		return "Savatchangiz bo`sh !\n Menyudan buyurtma qilishingiz mumkin", main_menu
	
	for kategory, product_id in cart[user_id]:
		if (kategory, product_id) in counts:
			counts[(kategory, product_id)] += 1
		else:
			counts[(kategory, product_id)] = 1
	
	for (kategory, product_id), quantity in counts.items():
		i += 1
		food = foods[kategory][product_id]
		text += f"{i}) {food['name']} x{quantity} - {food['price'] * quantity} somoni\n\n"
		total += food['price'] * quantity
		
		keyboard.button(text=f"{i} -", callback_data=f"remove_{kategory}_{product_id}")
		keyboard.button(text=f"{i} +", callback_data=f"add_{kategory}_{product_id}")
	

	text +=	f"\n\nJami narxi: {total}"
	keyboard.button(text="Tozalash", callback_data="clear_cart")
	keyboard.button(text="Orqaga", callback_data="back")
	keyboard.adjust(2)
	klaviatura = keyboard.as_markup()
	
	return text, klaviatura
