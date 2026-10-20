from data import CATEGORY_NAMES


def cart_text(items: list[dict], currency: str = "сомони") -> str:
    if not items:
        return "🛒 Ваша корзина пуста. Откройте меню и добавьте товары."
    lines = ["🛒 <b>Ваша корзина</b>", ""]
    total = 0
    for index, item in enumerate(items, 1):
        lines.append(
            f"{index}. {item['name']} — {item['quantity']} × {item['unit_price']} = {item['line_total']} {currency}"
        )
        total += item["line_total"]
    lines.extend(["", f"<b>Итого: {total} {currency}</b>"])
    return "\n".join(lines)
