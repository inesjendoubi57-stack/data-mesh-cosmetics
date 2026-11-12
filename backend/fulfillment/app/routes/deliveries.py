
import sqlite3
from fastapi import APIRouter, HTTPException
from app import database
from app.schemas.delivery import Delivery

router = APIRouter()

@router.get("/")
def get_deliveries():
    return database.list_deliveries()

@router.get("/{order_id}")
def get_delivery(order_id: str):
    delivery = database.get_delivery(order_id)
    if delivery is None:
        raise HTTPException(status_code=404, detail="Order not found")
    return delivery

@router.post("/")
def create_delivery(delivery: Delivery):
    try:
        database.create_delivery(delivery)
    except sqlite3.IntegrityError as error:
        raise HTTPException(status_code=400, detail="Order already exists") from error
    return database.get_delivery(delivery.order_id)

@router.put("/{order_id}")
def update_delivery(order_id: str, delivery: Delivery):
    if database.get_delivery(order_id) is None:
        raise HTTPException(status_code=404, detail="Order not found")
    if order_id != delivery.order_id:
        raise HTTPException(status_code=400, detail="Order ID mismatch")
    if not database.update_delivery(delivery):
        raise HTTPException(status_code=404, detail="Order not found")
    return database.get_delivery(delivery.order_id)

@router.delete("/{order_id}")
def delete_delivery(order_id: str):
    if not database.delete_delivery(order_id):
        raise HTTPException(status_code=404, detail="Order not found")
    return {"message": "Order deleted successfully"}
