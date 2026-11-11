import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

from app.schemas.product import Product

DATABASE_PATH = Path(__file__).resolve().parent.parent / "products.db"

INITIAL_PRODUCTS = (
    Product(
        product_id="1",
        name="Lipstick",
        brand="Maybelline",
        category="Makeup",
        price=25.5,
        volume_ml=None,
        stock_qty=50,
    ),
    Product(
        product_id="2",
        name="Face Cream",
        brand="Nivea",
        category="Skincare",
        price=40.0,
        volume_ml=50,
        stock_qty=30,
    ),
)


@contextmanager
def get_connection() -> Iterator[sqlite3.Connection]:
    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row
    try:
        yield connection
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def initialize_database() -> None:
    with get_connection() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS products (
                product_id TEXT PRIMARY KEY,
                name TEXT NOT NULL CHECK (length(name) >= 2),
                brand TEXT NOT NULL,
                category TEXT NOT NULL,
                price REAL NOT NULL CHECK (price > 0),
                volume_ml INTEGER,
                stock_qty INTEGER NOT NULL CHECK (stock_qty >= 0)
            )
            """
        )
        product_count = connection.execute(
            "SELECT COUNT(*) FROM products"
        ).fetchone()[0]
        if product_count == 0:
            connection.executemany(
                """
                INSERT INTO products (
                    product_id, name, brand, category, price, volume_ml, stock_qty
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                [
                    (
                        product.product_id,
                        product.name,
                        product.brand,
                        product.category,
                        product.price,
                        product.volume_ml,
                        product.stock_qty,
                    )
                    for product in INITIAL_PRODUCTS
                ],
            )


def list_products() -> list[Product]:
    with get_connection() as connection:
        rows = connection.execute(
            "SELECT * FROM products ORDER BY product_id"
        ).fetchall()
    return [Product(**dict(row)) for row in rows]


def get_product(product_id: str) -> Product | None:
    with get_connection() as connection:
        row = connection.execute(
            "SELECT * FROM products WHERE product_id = ?",
            (product_id,),
        ).fetchone()
    return Product(**dict(row)) if row is not None else None


def create_product(product: Product) -> None:
    with get_connection() as connection:
        connection.execute(
            """
            INSERT INTO products (
                product_id, name, brand, category, price, volume_ml, stock_qty
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                product.product_id,
                product.name,
                product.brand,
                product.category,
                product.price,
                product.volume_ml,
                product.stock_qty,
            ),
        )


def update_product(product: Product) -> bool:
    with get_connection() as connection:
        cursor = connection.execute(
            """
            UPDATE products
            SET name = ?, brand = ?, category = ?, price = ?, volume_ml = ?, stock_qty = ?
            WHERE product_id = ?
            """,
            (
                product.name,
                product.brand,
                product.category,
                product.price,
                product.volume_ml,
                product.stock_qty,
                product.product_id,
            ),
        )
    return cursor.rowcount > 0


def delete_product(product_id: str) -> bool:
    with get_connection() as connection:
        cursor = connection.execute(
            "DELETE FROM products WHERE product_id = ?",
            (product_id,),
        )
    return cursor.rowcount > 0
