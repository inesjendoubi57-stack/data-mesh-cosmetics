
from fastapi import APIRouter, HTTPException
from app.schemas.product import Product

router = APIRouter()

# Données temporaires des produits
products = {
    1: Product(
        product_id=1,
        product_name="Lipstick",
        brand="Maybelline",
        price=25.5,
        category="Makeup"
    ),
    2: Product(
        product_id=2,
        product_name="Face Cream",
        brand="Nivea",
        price=40.0,
        category="Skincare"
    )
}


# GET : récupérer tous les produits
@router.get("/")
def get_products():
    return list(products.values())


# GET : récupérer un produit par ID
@router.get("/{product_id}")
def get_product(product_id: int):
    if product_id not in products:
        raise HTTPException(
            status_code=404,
            detail="Product not found"
        )
    return products[product_id]


# POST : ajouter un produit
@router.post("/")
def add_product(product: Product):
    if product.product_id in products:
        raise HTTPException(
            status_code=400,
            detail="Product already exists"
        )

    products[product.product_id] = product

    return {
        "message": "Product added successfully",
        "product": product
    }


# PUT : modifier un produit
@router.put("/{product_id}")
def update_product(product_id: int, product: Product):
    if product_id not in products:
        raise HTTPException(
            status_code=404,
            detail="Product not found"
        )

    if product.product_id != product_id:
        raise HTTPException(
            status_code=400,
            detail="Product ID mismatch"
        )

    products[product_id] = product

    return {
        "message": "Product updated successfully",
        "product": product
    }


# DELETE : supprimer un produit
@router.delete("/{product_id}")
def delete_product(product_id: int):
    if product_id not in products:
        raise HTTPException(
            status_code=404,
            detail="Product not found"
        )

    del products[product_id]

    return {
        "message": "Product deleted successfully"
    }
