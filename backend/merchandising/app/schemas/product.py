
from datetime import datetime, timezone

from pydantic import BaseModel, Field, field_validator


class ProductInput(BaseModel):
    product_id: str
    name: str = Field(min_length=2)
    brand: str
    category: str
    price: float = Field(gt=0)
    volume_ml: int | None = None
    stock_qty: int = Field(ge=0)


class Product(ProductInput):
    updated_at: datetime

    @field_validator("updated_at")
    @classmethod
    def normalize_updated_at(cls, value: datetime) -> datetime:
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)
