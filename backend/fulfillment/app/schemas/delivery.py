
from datetime import datetime, timezone
from pydantic import BaseModel, Field


class Delivery(BaseModel):
    order_id: str
    product_id: str
    quantity: int = Field(gt=0)
    status: str
    carrier: str | None = None
    shipped_at: datetime | None = None
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
