
import sqlite3

from fastapi import APIRouter, HTTPException
from app import database
from app.schemas.product import Product, ProductInput

router = APIRouter()

@router.get("/", response_model=list[Product])
def get_products():
    return database.list_products()

@router.get("/{product_id}", response_model=Product)
def get_product(product_id: str):
    product = database.get_product(product_id)
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    return product

@router.post("/", response_model=Product)
def create_product(product: ProductInput):
    try:
        database.create_product(product)
    except sqlite3.IntegrityError as error:
        raise HTTPException(status_code=400, detail="Product already exists") from error
    created = database.get_product(product.product_id)
    if created is None:
        raise HTTPException(status_code=500, detail="Created product could not be read")
    return created

@router.put("/{product_id}", response_model=Product)
def update_product(product_id: str, product: ProductInput):
    if product_id != product.product_id:
        raise HTTPException(status_code=400, detail="Product ID mismatch")
    if not database.update_product(product):
        raise HTTPException(status_code=404, detail="Product not found")
    updated = database.get_product(product.product_id)
    if updated is None:
        raise HTTPException(status_code=500, detail="Updated product could not be read")
    return updated

@router.delete("/{product_id}")
def delete_product(product_id: str):
    if not database.delete_product(product_id):
        raise HTTPException(status_code=404, detail="Product not found")
    return {"message": "Product deleted successfully"}
