
from datetime import datetime, timezone

from pydantic import BaseModel, Field


class Product(BaseModel):
    product_id: str
    name: str = Field(min_length=2)
    brand: str
    category: str
    price: float = Field(gt=0)
    volume_ml: int | None = None
    stock_qty: int = Field(ge=0)
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
