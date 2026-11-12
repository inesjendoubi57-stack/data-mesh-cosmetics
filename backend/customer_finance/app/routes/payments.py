
import sqlite3

from fastapi import APIRouter, HTTPException
from app import database
from app.schemas.payment import Payment, PaymentInput

router = APIRouter()

@router.get("/", response_model=list[Payment])
def get_payments():
    return database.list_payments()

@router.get("/{invoice_id}", response_model=Payment)
def get_payment(invoice_id: str):
    payment = database.get_payment(invoice_id)
    if payment is None:
        raise HTTPException(status_code=404, detail="Invoice not found")
    return payment

@router.post("/", response_model=Payment)
def create_payment(payment: PaymentInput):
    try:
        database.create_payment(payment)
    except sqlite3.IntegrityError as error:
        raise HTTPException(status_code=400, detail="Invoice already exists") from error
    created = database.get_payment(payment.invoice_id)
    if created is None:
        raise HTTPException(status_code=500, detail="Created payment could not be read")
    return created

@router.put("/{invoice_id}", response_model=Payment)
def update_payment(invoice_id: str, payment: PaymentInput):
    if database.get_payment(invoice_id) is None:
        raise HTTPException(status_code=404, detail="Invoice not found")
    if invoice_id != payment.invoice_id:
        raise HTTPException(status_code=400, detail="Invoice ID mismatch")
    if not database.update_payment(payment):
        raise HTTPException(status_code=404, detail="Invoice not found")
    updated = database.get_payment(payment.invoice_id)
    if updated is None:
        raise HTTPException(status_code=500, detail="Updated payment could not be read")
    return updated

@router.delete("/{invoice_id}")
def delete_payment(invoice_id: str):
    if not database.delete_payment(invoice_id):
        raise HTTPException(status_code=404, detail="Invoice not found")
    return {"message": "Invoice deleted successfully"}
