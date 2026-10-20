"""Restaurant product catalog. Edit product names, descriptions and prices here."""
foods = {
    "pizza": {
        "margarita": {"name": "Маргарита", "description": "Классическая пицца с томатным соусом, моцареллой и свежим базиликом.", "price": 35},
        "pepperoni": {"name": "Пепперони", "description": "Пицца с томатным соусом, моцареллой и колбасой пепперони.", "price": 40},
        "chiken": {"name": "Чикен", "description": "Пицца с моцареллой, чеддером, пармезаном и сыром дорблю.", "price": 45},
        "cheese": {"name": "Сырная", "description": "Нежная пицца с моцареллой, чеддером и пармезаном.", "price": 45},
        "meat_pizza": {"name": "Мясная пицца", "description": "Пицца с говядиной, пепперони, колбасой, моцареллой и фирменным соусом.", "price": 50},
    },
    "burger": {
        "cheesburger": {"name": "Чизбургер", "description": "Говяжья котлета, чеддер, помидор, огурец и фирменный соус.", "price": 30},
        "chicken_burger": {"name": "Чикен-бургер", "description": "Хрустящая курица, свежий салат, помидор и фирменный соус.", "price": 30},
        "double_burger": {"name": "Двойной бургер", "description": "Две говяжьи котлеты, чеддер, свежие овощи и фирменный соус.", "price": 45},
    },
    "ichimlik": {
        "coca_cola": {"name": "Coca-Cola", "description": "Классическая охлаждённая Coca-Cola.", "price": 10},
        "fanta": {"name": "Fanta", "description": "Газированный напиток со вкусом апельсина.", "price": 10},
        "sprite": {"name": "Sprite", "description": "Освежающий напиток со вкусом лимона и лайма.", "price": 10},
        "apelsin_sharbat": {"name": "Апельсиновый сок", "description": "Сок с приятным апельсиновым вкусом.", "price": 15},
        "olma_sharbat": {"name": "Яблочный сок", "description": "Освежающий яблочный сок.", "price": 15},
    },
}

CATEGORY_NAMES = {"pizza": "Пиццы", "burger": "Бургеры", "ichimlik": "Напитки"}


def get_product(category: str, product_id: str) -> dict | None:
    """Return a product only when both category and product identifier exist."""
    return foods.get(category, {}).get(product_id)
