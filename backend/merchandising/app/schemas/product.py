
from pydantic import BaseModel, Field

class Product(BaseModel):
    product_id: str
    name: str = Field(min_length=2)
    brand: str
    category: str
    price: float = Field(gt=0)
    volume_ml: int | None = None
    stock_qty: int = Field(ge=0)
