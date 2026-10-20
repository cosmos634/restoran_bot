import pytest

from config import get_settings
from data import get_product
from database import (
    add_to_cart, adjust_cart, clear_cart, create_order, get_cart,
    get_order_items, order_history, init_db,
)
from handlers.admin import is_admin
from handlers.checkout import Checkout


@pytest.fixture
def db_path(tmp_path):
    path = str(tmp_path / "test.sqlite3")
    init_db(path)
    return path


def test_product_lookup_and_unknown_ids():
    assert get_product("pizza", "meat_pizza")["price"] == 50
    assert get_product("pizza", "does_not_exist") is None
    assert get_product("unknown", "margarita") is None


def test_cart_isolation_and_quantity_operations(db_path):
    assert add_to_cart(10, "burger", "chicken_burger", db_path)
    assert add_to_cart(10, "burger", "chicken_burger", db_path)
    assert add_to_cart(20, "burger", "chicken_burger", db_path)
    assert get_cart(10, db_path)[0]["quantity"] == 2
    assert get_cart(20, db_path)[0]["quantity"] == 1
    assert adjust_cart(10, "burger", "chicken_burger", -1, db_path)
    assert get_cart(10, db_path)[0]["quantity"] == 1
    assert adjust_cart(10, "burger", "chicken_burger", -1, db_path)
    assert get_cart(10, db_path) == []
    assert not adjust_cart(10, "burger", "chicken_burger", -1, db_path)


def test_totals_empty_cart_and_clear(db_path):
    assert get_cart(1, db_path) == []
    assert add_to_cart(1, "pizza", "margarita", db_path)
    assert add_to_cart(1, "pizza", "margarita", db_path)
    assert add_to_cart(1, "ichimlik", "fanta", db_path)
    items = get_cart(1, db_path)
    assert sum(item["line_total"] for item in items) == 80
    clear_cart(1, db_path)
    assert get_cart(1, db_path) == []


def test_order_persistence_duplicate_confirmation_and_history_isolation(db_path):
    add_to_cart(1, "pizza", "margarita", db_path)
    add_to_cart(1, "burger", "cheesburger", db_path)
    order = create_order(
        user_id=1, customer_name="Test User", phone="+992900000000",
        fulfillment="pickup", address="", confirmation_token="token-once", db_path=db_path,
    )
    assert order and order["total"] == 65
    assert get_cart(1, db_path) == []
    assert sum(item["line_total"] for item in get_order_items(order["id"], db_path)) == 65
    replay = create_order(
        user_id=1, customer_name="Test User", phone="+992900000000",
        fulfillment="pickup", address="", confirmation_token="token-once", db_path=db_path,
    )
    assert replay["id"] == order["id"]
    assert len(order_history(1, db_path)) == 1
    assert order_history(2, db_path) == []
    init_db(db_path)
    assert len(order_history(1, db_path)) == 1


def test_checkout_validation_and_delivery_address(db_path):
    with pytest.raises(ValueError):
        create_order(user_id=1, customer_name="", phone="1234567", fulfillment="pickup",
                     address="", confirmation_token="bad-name", db_path=db_path)
    with pytest.raises(ValueError):
        create_order(user_id=1, customer_name="Test", phone="1234567", fulfillment="delivery",
                     address="", confirmation_token="bad-address", db_path=db_path)


def test_invalid_product_is_not_added(db_path):
    assert not add_to_cart(1, "pizza", "not_real", db_path)
    assert get_cart(1, db_path) == []


def test_config_missing_token_and_admin_authorization():
    with pytest.raises(ValueError, match="BOT_TOKEN"):
        get_settings({})
    settings = get_settings({
        "BOT_TOKEN": "123456:abcdefghijklmnopqrstuvwxyzABCDEF",
        "ADMIN_IDS": "123, 456",
        "DATABASE_PATH": "tmp.db",
    })
    assert settings.admin_ids == frozenset({123, 456})
    with pytest.raises(ValueError, match="ADMIN_IDS"):
        get_settings({"BOT_TOKEN": "123456:abcdefghijklmnopqrstuvwxyzABCDEF", "ADMIN_IDS": "abc"})
    assert is_admin(123, settings.admin_ids)
    assert not is_admin(999, settings.admin_ids)


def test_checkout_state_definitions_exist():
    assert Checkout.name is not None
    assert Checkout.phone is not None
    assert Checkout.fulfillment is not None
    assert Checkout.address is not None
    assert Checkout.review is not None
