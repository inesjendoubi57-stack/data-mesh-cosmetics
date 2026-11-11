
import sqlite3

from fastapi import APIRouter, HTTPException
from app import database
from app.schemas.product import Product

router = APIRouter()

@router.get("/")
def get_products():
    return database.list_products()

@router.get("/{product_id}")
def get_product(product_id: str):
    product = database.get_product(product_id)
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    return product

@router.post("/")
def create_product(product: Product):
    try:
        database.create_product(product)
    except sqlite3.IntegrityError as error:
        raise HTTPException(status_code=400, detail="Product already exists") from error
    return product

@router.put("/{product_id}")
def update_product(product_id: str, product: Product):
    if product_id != product.product_id:
        raise HTTPException(status_code=400, detail="Product ID mismatch")
    if not database.update_product(product):
        raise HTTPException(status_code=404, detail="Product not found")
    return product

@router.delete("/{product_id}")
def delete_product(product_id: str):
    if not database.delete_product(product_id):
        raise HTTPException(status_code=404, detail="Product not found")
    return {"message": "Product deleted successfully"}
