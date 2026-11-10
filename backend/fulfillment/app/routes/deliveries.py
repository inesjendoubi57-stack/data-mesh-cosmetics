
from fastapi import APIRouter, HTTPException
from app.schemas.delivery import Delivery
from datetime import datetime

router = APIRouter()

deliveries = {
    "1": Delivery(
        order_id="1",
        product_id="1",
        quantity=2,
        status="Pending",
        carrier=None,
        shipped_at=None
    ),
    "2": Delivery(
        order_id="2",
        product_id="2",
        quantity=1,
        status="Delivered",
        carrier="DHL",
        shipped_at=datetime(2026, 11, 9, 10, 0)
    )
}

@router.get("/")
def get_deliveries():
    return list(deliveries.values())

@router.get("/{order_id}")
def get_delivery(order_id: str):
    if order_id not in deliveries:
        raise HTTPException(status_code=404, detail="Order not found")
    return deliveries[order_id]

@router.post("/")
def create_delivery(delivery: Delivery):
    if delivery.order_id in deliveries:
        raise HTTPException(status_code=400, detail="Order already exists")
    deliveries[delivery.order_id] = delivery
    return delivery

@router.put("/{order_id}")
def update_delivery(order_id: str, delivery: Delivery):
    if order_id not in deliveries:
        raise HTTPException(status_code=404, detail="Order not found")
    if order_id != delivery.order_id:
        raise HTTPException(status_code=400, detail="Order ID mismatch")
    deliveries[order_id] = delivery
    return delivery

@router.delete("/{order_id}")
def delete_delivery(order_id: str):
    if order_id not in deliveries:
        raise HTTPException(status_code=404, detail="Order not found")
    del deliveries[order_id]
    return {"message": "Order deleted successfully"}
