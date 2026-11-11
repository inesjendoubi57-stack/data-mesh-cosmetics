
from datetime import datetime
from pydantic import BaseModel, Field

class Delivery(BaseModel):
    order_id: str
    product_id: str
    quantity: int = Field(gt=0)
    status: str
    carrier: str | None = None
    shipped_at: datetime | None = None
