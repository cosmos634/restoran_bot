"""Small SQLite data layer for carts and orders."""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import secrets
import sqlite3

from data import foods, get_product


def connect(db_path: str) -> sqlite3.Connection:
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(db_path, timeout=10, isolation_level=None)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    connection.execute("PRAGMA busy_timeout = 10000")
    return connection


def init_db(db_path: str) -> None:
    with connect(db_path) as db:
        db.executescript("""
        PRAGMA journal_mode = WAL;
        CREATE TABLE IF NOT EXISTS cart_items (
            user_id INTEGER NOT NULL,
            category TEXT NOT NULL,
            product_id TEXT NOT NULL,
            quantity INTEGER NOT NULL CHECK (quantity > 0),
            PRIMARY KEY (user_id, category, product_id)
        );
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_number TEXT NOT NULL UNIQUE,
            confirmation_token TEXT NOT NULL UNIQUE,
            user_id INTEGER NOT NULL,
            customer_name TEXT NOT NULL,
            phone TEXT NOT NULL,
            fulfillment TEXT NOT NULL CHECK (fulfillment IN ('delivery', 'pickup')),
            address TEXT NOT NULL DEFAULT '',
            total INTEGER NOT NULL CHECK (total >= 0),
            status TEXT NOT NULL DEFAULT 'pending',
            created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS order_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
            category TEXT NOT NULL,
            product_id TEXT NOT NULL,
            product_name TEXT NOT NULL,
            quantity INTEGER NOT NULL CHECK (quantity > 0),
            unit_price INTEGER NOT NULL CHECK (unit_price >= 0),
            line_total INTEGER NOT NULL CHECK (line_total >= 0)
        );
        CREATE INDEX IF NOT EXISTS idx_orders_user_created ON orders(user_id, created_at DESC);
        """)


def get_cart(user_id: int, db_path: str) -> list[dict]:
    with connect(db_path) as db:
        rows = db.execute(
            "SELECT category, product_id, quantity FROM cart_items WHERE user_id=? ORDER BY category, product_id",
            (user_id,),
        ).fetchall()
    items = []
    for row in rows:
        product = get_product(row["category"], row["product_id"])
        if product is None:
            continue
        quantity = row["quantity"]
        items.append({
            "category": row["category"], "product_id": row["product_id"],
            "name": product["name"], "quantity": quantity,
            "unit_price": product["price"], "line_total": product["price"] * quantity,
        })
    return items


def add_to_cart(user_id: int, category: str, product_id: str, db_path: str) -> bool:
    product = get_product(category, product_id)
    if product is None:
        return False
    with connect(db_path) as db:
        db.execute("""
            INSERT INTO cart_items(user_id, category, product_id, quantity) VALUES (?, ?, ?, 1)
            ON CONFLICT(user_id, category, product_id) DO UPDATE SET quantity=quantity+1
        """, (user_id, category, product_id))
    return True


def adjust_cart(user_id: int, category: str, product_id: str, delta: int, db_path: str) -> bool:
    if delta not in (-1, 1) or get_product(category, product_id) is None:
        return False
    with connect(db_path) as db:
        row = db.execute(
            "SELECT quantity FROM cart_items WHERE user_id=? AND category=? AND product_id=?",
            (user_id, category, product_id),
        ).fetchone()
        if row is None:
            return False
        if row["quantity"] + delta <= 0:
            db.execute(
                "DELETE FROM cart_items WHERE user_id=? AND category=? AND product_id=?",
                (user_id, category, product_id),
            )
        else:
            db.execute(
                "UPDATE cart_items SET quantity=quantity+? WHERE user_id=? AND category=? AND product_id=?",
                (delta, user_id, category, product_id),
            )
    return True


def clear_cart(user_id: int, db_path: str) -> None:
    with connect(db_path) as db:
        db.execute("DELETE FROM cart_items WHERE user_id=?", (user_id,))


def create_order(
    *, user_id: int, customer_name: str, phone: str, fulfillment: str,
    address: str, confirmation_token: str, db_path: str,
) -> dict | None:
    """Atomically snapshot trusted catalog prices, create one order, and empty the cart.

    Returns the existing order if the same confirmation token is replayed.
    """
    if fulfillment not in {"delivery", "pickup"}:
        raise ValueError("Invalid fulfillment type")
    if not customer_name.strip() or not phone.strip():
        raise ValueError("Name and phone are required")
    if fulfillment == "delivery" and not address.strip():
        raise ValueError("Delivery address is required")
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    with connect(db_path) as db:
        db.execute("BEGIN IMMEDIATE")
        existing = db.execute(
            "SELECT * FROM orders WHERE confirmation_token=?", (confirmation_token,)
        ).fetchone()
        if existing:
            db.execute("COMMIT")
            return dict(existing)
        rows = db.execute(
            "SELECT category, product_id, quantity FROM cart_items WHERE user_id=? ORDER BY category, product_id",
            (user_id,),
        ).fetchall()
        if not rows:
            db.execute("ROLLBACK")
            return None
        items = []
        total = 0
        for row in rows:
            product = get_product(row["category"], row["product_id"])
            if product is None:
                continue
            line_total = product["price"] * row["quantity"]
            total += line_total
            items.append((row["category"], row["product_id"], product["name"], row["quantity"], product["price"], line_total))
        if not items:
            db.execute("ROLLBACK")
            return None
        order_number = f"R{datetime.now(timezone.utc):%y%m%d}-{secrets.token_hex(3).upper()}"
        cursor = db.execute("""
            INSERT INTO orders(order_number, confirmation_token, user_id, customer_name, phone,
                fulfillment, address, total, status, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'pending', ?)
        """, (order_number, confirmation_token, user_id, customer_name.strip(), phone.strip(),
              fulfillment, address.strip() if fulfillment == "delivery" else "", total, now))
        order_id = cursor.lastrowid
        db.executemany("""
            INSERT INTO order_items(order_id, category, product_id, product_name, quantity, unit_price, line_total)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, [(order_id, *item) for item in items])
        db.execute("DELETE FROM cart_items WHERE user_id=?", (user_id,))
        order = dict(db.execute("SELECT * FROM orders WHERE id=?", (order_id,)).fetchone())
        db.execute("COMMIT")
        return order


def get_order_items(order_id: int, db_path: str) -> list[dict]:
    with connect(db_path) as db:
        rows = db.execute(
            "SELECT category, product_id, product_name, quantity, unit_price, line_total FROM order_items WHERE order_id=? ORDER BY id",
            (order_id,),
        ).fetchall()
    return [dict(row) for row in rows]


def order_history(user_id: int, db_path: str) -> list[dict]:
    with connect(db_path) as db:
        rows = db.execute(
            "SELECT * FROM orders WHERE user_id=? ORDER BY created_at DESC, id DESC", (user_id,)
        ).fetchall()
    return [dict(row) for row in rows]


def get_order_by_number(order_number: str, db_path: str) -> dict | None:
    with connect(db_path) as db:
        row = db.execute("SELECT * FROM orders WHERE order_number=?", (order_number,)).fetchone()
    return dict(row) if row else None


def list_orders(db_path: str, limit: int = 15) -> list[dict]:
    """Return the newest orders for the admin panel."""
    limit = max(1, min(int(limit), 50))
    with connect(db_path) as db:
        rows = db.execute(
            "SELECT * FROM orders ORDER BY created_at DESC, id DESC LIMIT ?", (limit,)
        ).fetchall()
    return [dict(row) for row in rows]


def order_stats(db_path: str) -> dict:
    """Return order counts and revenue from non-cancelled orders."""
    with connect(db_path) as db:
        row = db.execute("""
            SELECT COUNT(*) AS total,
                   SUM(CASE WHEN status='pending' THEN 1 ELSE 0 END) AS pending,
                   SUM(CASE WHEN status='accepted' THEN 1 ELSE 0 END) AS accepted,
                   SUM(CASE WHEN status='preparing' THEN 1 ELSE 0 END) AS preparing,
                   SUM(CASE WHEN status='completed' THEN 1 ELSE 0 END) AS completed,
                   SUM(CASE WHEN status='cancelled' THEN 1 ELSE 0 END) AS cancelled,
                   COALESCE(SUM(CASE WHEN status!='cancelled' THEN total ELSE 0 END), 0) AS revenue
            FROM orders
        """).fetchone()
    return {key: (row[key] or 0) for key in row.keys()}


def update_order_status(order_number: str, status: str, db_path: str) -> bool:
    allowed = {"pending", "accepted", "preparing", "completed", "cancelled"}
    if status not in allowed:
        return False
    with connect(db_path) as db:
        cursor = db.execute("UPDATE orders SET status=? WHERE order_number=?", (status, order_number))
    return cursor.rowcount == 1
