
import sqlite3

from fastapi import APIRouter, HTTPException
from app import database
from app.schemas.payment import Payment

router = APIRouter()

@router.get("/")
def get_payments():
    return database.list_payments()

@router.get("/{invoice_id}")
def get_payment(invoice_id: str):
    payment = database.get_payment(invoice_id)
    if payment is None:
        raise HTTPException(status_code=404, detail="Invoice not found")
    return payment

@router.post("/")
def create_payment(payment: Payment):
    try:
        database.create_payment(payment)
    except sqlite3.IntegrityError as error:
        raise HTTPException(status_code=400, detail="Invoice already exists") from error
    return database.get_payment(payment.invoice_id)

@router.put("/{invoice_id}")
def update_payment(invoice_id: str, payment: Payment):
    if database.get_payment(invoice_id) is None:
        raise HTTPException(status_code=404, detail="Invoice not found")
    if invoice_id != payment.invoice_id:
        raise HTTPException(status_code=400, detail="Invoice ID mismatch")
    if not database.update_payment(payment):
        raise HTTPException(status_code=404, detail="Invoice not found")
    return database.get_payment(payment.invoice_id)

@router.delete("/{invoice_id}")
def delete_payment(invoice_id: str):
    if not database.delete_payment(invoice_id):
        raise HTTPException(status_code=404, detail="Invoice not found")
    return {"message": "Invoice deleted successfully"}
