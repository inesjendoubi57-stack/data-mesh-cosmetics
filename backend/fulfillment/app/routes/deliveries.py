
import sqlite3
from pathlib import Path

import yaml
from fastapi import APIRouter, HTTPException
from app import database
from app.schemas.delivery import Delivery, DeliveryInput

router = APIRouter()

CONTRACT_PATH = Path(__file__).resolve().parents[4] / "contracts" / "fulfillment-orders.yaml"

@router.get("/", response_model=list[Delivery])
def get_deliveries():
    return database.list_deliveries()

@router.get("/contract")
def get_contract():
    with open(CONTRACT_PATH, "r", encoding="utf-8") as file:
        return yaml.safe_load(file)

@router.get("/{order_id}", response_model=Delivery)
def get_delivery(order_id: str):
    delivery = database.get_delivery(order_id)
    if delivery is None:
        raise HTTPException(status_code=404, detail="Order not found")
    return delivery

@router.post("/", response_model=Delivery)
def create_delivery(delivery: DeliveryInput):
    try:
        database.create_delivery(delivery)
    except sqlite3.IntegrityError as error:
        raise HTTPException(status_code=400, detail="Order already exists") from error
    created = database.get_delivery(delivery.order_id)
    if created is None:
        raise HTTPException(status_code=500, detail="Created delivery could not be read")
    return created

@router.put("/{order_id}", response_model=Delivery)
def update_delivery(order_id: str, delivery: DeliveryInput):
    if database.get_delivery(order_id) is None:
        raise HTTPException(status_code=404, detail="Order not found")
    if order_id != delivery.order_id:
        raise HTTPException(status_code=400, detail="Order ID mismatch")
    if not database.update_delivery(delivery):
        raise HTTPException(status_code=404, detail="Order not found")
    updated = database.get_delivery(delivery.order_id)
    if updated is None:
        raise HTTPException(status_code=500, detail="Updated delivery could not be read")
    return updated

@router.delete("/{order_id}")
def delete_delivery(order_id: str):
    if not database.delete_delivery(order_id):
        raise HTTPException(status_code=404, detail="Order not found")
    return {"message": "Order deleted successfully"}
