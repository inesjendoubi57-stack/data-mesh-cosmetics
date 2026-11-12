
from datetime import datetime, timezone
from pydantic import BaseModel, Field, field_validator


class DeliveryInput(BaseModel):
    order_id: str
    product_id: str
    quantity: int = Field(gt=0)
    status: str
    carrier: str | None = None
    shipped_at: datetime | None = None


class Delivery(DeliveryInput):
    updated_at: datetime

    @field_validator("updated_at")
    @classmethod
    def normalize_updated_at(cls, value: datetime) -> datetime:
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)

    @field_validator("shipped_at")
    @classmethod
    def normalize_shipped_at(cls, value: datetime | None) -> datetime | None:
        if value is None:
            return None
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)
