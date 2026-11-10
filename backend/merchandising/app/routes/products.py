
from fastapi import APIRouter, HTTPException
from app.schemas.product import Product

router = APIRouter()

products = {
    "1": Product(
        product_id="1",
        name="Lipstick",
        brand="Maybelline",
        category="Makeup",
        price=25.5,
        volume_ml=None,
        stock_qty=50
    ),
    "2": Product(
        product_id="2",
        name="Face Cream",
        brand="Nivea",
        category="Skincare",
        price=40.0,
        volume_ml=50,
        stock_qty=30
    )
}

@router.get("/")
def get_products():
    return list(products.values())

@router.get("/{product_id}")
def get_product(product_id: str):
    if product_id not in products:
        raise HTTPException(status_code=404, detail="Product not found")
    return products[product_id]

@router.post("/")
def create_product(product: Product):
    if product.product_id in products:
        raise HTTPException(status_code=400, detail="Product already exists")
    products[product.product_id] = product
    return product

@router.put("/{product_id}")
def update_product(product_id: str, product: Product):
    if product_id not in products:
        raise HTTPException(status_code=404, detail="Product not found")
    if product_id != product.product_id:
        raise HTTPException(status_code=400, detail="Product ID mismatch")
    products[product_id] = product
    return product

@router.delete("/{product_id}")
def delete_product(product_id: str):
    if product_id not in products:
        raise HTTPException(status_code=404, detail="Product not found")
    del products[product_id]
    return {"message": "Product deleted successfully"}
