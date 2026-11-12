
from datetime import datetime, timezone

from pydantic import BaseModel, Field


class Payment(BaseModel):
    invoice_id: str
    order_id: str
    amount: float = Field(gt=0)
    currency: str
    payment_method: str
    payment_status: str
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
