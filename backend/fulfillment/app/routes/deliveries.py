
from fastapi import APIRouter, HTTPException
from app.schemas.delivery import Delivery

router = APIRouter()

# Données temporaires des livraisons
deliveries = {
    1: Delivery(
        order_id=1,
        product_id=1,
        quantity=2,
        delivery_status="Pending"
    ),
    2: Delivery(
        order_id=2,
        product_id=2,
        quantity=1,
        delivery_status="Delivered"
    )
}

# GET : récupérer toutes les livraisons
@router.get("/")
def get_deliveries():
    return list(deliveries.values())


# GET : récupérer une livraison par ID
@router.get("/{order_id}")
def get_delivery(order_id: int):
    if order_id not in deliveries:
        raise HTTPException(
            status_code=404,
            detail="Delivery not found"
        )
    return deliveries[order_id]


# POST : ajouter une livraison
@router.post("/")
def add_delivery(delivery: Delivery):
    if delivery.order_id in deliveries:
        raise HTTPException(
            status_code=400,
            detail="Delivery already exists"
        )

    deliveries[delivery.order_id] = delivery

    return {
        "message": "Delivery added successfully",
        "delivery": delivery
    }


# PUT : modifier une livraison
@router.put("/{order_id}")
def update_delivery(order_id: int, delivery: Delivery):
    if order_id not in deliveries:
        raise HTTPException(
            status_code=404,
            detail="Delivery not found"
        )

    if delivery.order_id != order_id:
        raise HTTPException(
            status_code=400,
            detail="Order ID mismatch"
        )

    deliveries[order_id] = delivery

    return {
        "message": "Delivery updated successfully",
        "delivery": delivery
    }


# DELETE : supprimer une livraison
@router.delete("/{order_id}")
def delete_delivery(order_id: int):
    if order_id not in deliveries:
        raise HTTPException(
            status_code=404,
            detail="Delivery not found"
        )

    del deliveries[order_id]

    return {
        "message": "Delivery deleted successfully"
    }
