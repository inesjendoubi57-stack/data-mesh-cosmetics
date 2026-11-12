
from datetime import datetime, timezone

from pydantic import BaseModel, Field, field_validator


class PaymentInput(BaseModel):
    invoice_id: str
    order_id: str
    amount: float = Field(gt=0)
    currency: str
    payment_method: str
    payment_status: str


class Payment(PaymentInput):
    updated_at: datetime

    @field_validator("updated_at")
    @classmethod
    def normalize_updated_at(cls, value: datetime) -> datetime:
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)
