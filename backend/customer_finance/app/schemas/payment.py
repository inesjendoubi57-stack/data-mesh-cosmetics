
from pydantic import BaseModel, Field

class Payment(BaseModel):
    payment_id: int
    customer_id: int
    amount: float = Field(gt=0)
    payment_status: str
