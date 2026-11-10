from pydantic import BaseModel, Field

class Delivery(BaseModel):
    order_id: int
    product_id: int
    quantity: int = Field(gt=0)
    delivery_status: str