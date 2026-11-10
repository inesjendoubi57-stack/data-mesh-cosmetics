from pydantic import BaseModel, Field


class Product(BaseModel):
    product_id: int
    product_name: str = Field(min_length=2)
    brand: str
    price: float = Field(gt=0)
    category: str