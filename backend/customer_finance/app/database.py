import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterator

from app.schemas.payment import Payment

DATABASE_PATH = Path(__file__).resolve().parent.parent / "customer_finance.db"

INITIAL_PAYMENTS = (
    Payment(
        invoice_id="1",
        order_id="101",
        amount=120.5,
        currency="TND",
        payment_method="Card",
        payment_status="Paid",
    ),
    Payment(
        invoice_id="2",
        order_id="102",
        amount=75.0,
        currency="TND",
        payment_method="Cash",
        payment_status="Pending",
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
            CREATE TABLE IF NOT EXISTS payments (
                invoice_id TEXT PRIMARY KEY,
                order_id TEXT NOT NULL,
                amount REAL NOT NULL CHECK (amount > 0),
                currency TEXT NOT NULL,
                payment_method TEXT NOT NULL,
                payment_status TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )
        columns = {
            row["name"] for row in connection.execute("PRAGMA table_info(payments)")
        }
        if "updated_at" not in columns:
            connection.execute("ALTER TABLE payments ADD COLUMN updated_at TEXT")
        connection.execute(
            "UPDATE payments SET updated_at = ? WHERE updated_at IS NULL",
            (datetime.now(timezone.utc).isoformat(),),
        )
        payment_count = connection.execute(
            "SELECT COUNT(*) FROM payments"
        ).fetchone()[0]
        if payment_count == 0:
            connection.executemany(
                """
                INSERT INTO payments (
                    invoice_id, order_id, amount, currency, payment_method, payment_status,
                    updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                [
                    (
                        payment.invoice_id,
                        payment.order_id,
                        payment.amount,
                        payment.currency,
                        payment.payment_method,
                        payment.payment_status,
                        payment.updated_at.isoformat(),
                    )
                    for payment in INITIAL_PAYMENTS
                ],
            )


def list_payments() -> list[Payment]:
    with get_connection() as connection:
        rows = connection.execute(
            "SELECT * FROM payments ORDER BY rowid"
        ).fetchall()
    return [Payment(**dict(row)) for row in rows]


def get_payment(invoice_id: str) -> Payment | None:
    with get_connection() as connection:
        row = connection.execute(
            "SELECT * FROM payments WHERE invoice_id = ?",
            (invoice_id,),
        ).fetchone()
    return Payment(**dict(row)) if row is not None else None


def create_payment(payment: Payment) -> None:
    with get_connection() as connection:
        connection.execute(
            """
            INSERT INTO payments (
                invoice_id, order_id, amount, currency, payment_method, payment_status,
                updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                payment.invoice_id,
                payment.order_id,
                payment.amount,
                payment.currency,
                payment.payment_method,
                payment.payment_status,
                datetime.now(timezone.utc).isoformat(),
            ),
        )


def update_payment(payment: Payment) -> bool:
    with get_connection() as connection:
        cursor = connection.execute(
            """
            UPDATE payments
            SET order_id = ?, amount = ?, currency = ?, payment_method = ?, payment_status = ?,
                updated_at = ?
            WHERE invoice_id = ?
            """,
            (
                payment.order_id,
                payment.amount,
                payment.currency,
                payment.payment_method,
                payment.payment_status,
                datetime.now(timezone.utc).isoformat(),
                payment.invoice_id,
            ),
        )
    return cursor.rowcount > 0


def delete_payment(invoice_id: str) -> bool:
    with get_connection() as connection:
        cursor = connection.execute(
            "DELETE FROM payments WHERE invoice_id = ?",
            (invoice_id,),
        )
    return cursor.rowcount > 0
