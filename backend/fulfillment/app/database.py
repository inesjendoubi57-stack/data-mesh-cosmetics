import sqlite3
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Iterator

from app.schemas.delivery import Delivery

DATABASE_PATH = Path(__file__).resolve().parent.parent / "fulfillment.db"

INITIAL_DELIVERIES = (
    Delivery(
        order_id="1",
        product_id="1",
        quantity=2,
        status="Pending",
    ),
    Delivery(
        order_id="2",
        product_id="2",
        quantity=1,
        status="Delivered",
        carrier="DHL",
        shipped_at=datetime(2026, 11, 9, 10, 0),
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
            CREATE TABLE IF NOT EXISTS deliveries (
                order_id TEXT PRIMARY KEY,
                product_id TEXT NOT NULL,
                quantity INTEGER NOT NULL CHECK (quantity > 0),
                status TEXT NOT NULL,
                carrier TEXT,
                shipped_at TEXT
            )
            """
        )
        delivery_count = connection.execute(
            "SELECT COUNT(*) FROM deliveries"
        ).fetchone()[0]
        if delivery_count == 0:
            connection.executemany(
                """
                INSERT INTO deliveries (
                    order_id, product_id, quantity, status, carrier, shipped_at
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                [
                    (
                        delivery.order_id,
                        delivery.product_id,
                        delivery.quantity,
                        delivery.status,
                        delivery.carrier,
                        delivery.shipped_at.isoformat() if delivery.shipped_at else None,
                    )
                    for delivery in INITIAL_DELIVERIES
                ],
            )


def list_deliveries() -> list[Delivery]:
    with get_connection() as connection:
        rows = connection.execute(
            "SELECT * FROM deliveries ORDER BY rowid"
        ).fetchall()
    return [Delivery(**dict(row)) for row in rows]


def get_delivery(order_id: str) -> Delivery | None:
    with get_connection() as connection:
        row = connection.execute(
            "SELECT * FROM deliveries WHERE order_id = ?",
            (order_id,),
        ).fetchone()
    return Delivery(**dict(row)) if row is not None else None


def create_delivery(delivery: Delivery) -> None:
    with get_connection() as connection:
        connection.execute(
            """
            INSERT INTO deliveries (
                order_id, product_id, quantity, status, carrier, shipped_at
            ) VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                delivery.order_id,
                delivery.product_id,
                delivery.quantity,
                delivery.status,
                delivery.carrier,
                delivery.shipped_at.isoformat() if delivery.shipped_at else None,
            ),
        )


def update_delivery(delivery: Delivery) -> bool:
    with get_connection() as connection:
        cursor = connection.execute(
            """
            UPDATE deliveries
            SET product_id = ?, quantity = ?, status = ?, carrier = ?, shipped_at = ?
            WHERE order_id = ?
            """,
            (
                delivery.product_id,
                delivery.quantity,
                delivery.status,
                delivery.carrier,
                delivery.shipped_at.isoformat() if delivery.shipped_at else None,
                delivery.order_id,
            ),
        )
    return cursor.rowcount > 0


def delete_delivery(order_id: str) -> bool:
    with get_connection() as connection:
        cursor = connection.execute(
            "DELETE FROM deliveries WHERE order_id = ?",
            (order_id,),
        )
    return cursor.rowcount > 0
