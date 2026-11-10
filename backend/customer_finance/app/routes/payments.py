
from fastapi import APIRouter, HTTPException
from app.schemas.payment import Payment

router = APIRouter()

payments = {
    "1": Payment(
        invoice_id="1",
        order_id="101",
        amount=120.5,
        currency="TND",
        payment_method="Card",
        payment_status="Paid"
    ),
    "2": Payment(
        invoice_id="2",
        order_id="102",
        amount=75.0,
        currency="TND",
        payment_method="Cash",
        payment_status="Pending"
    )
}

@router.get("/")
def get_payments():
    return list(payments.values())

@router.get("/{invoice_id}")
def get_payment(invoice_id: str):
    if invoice_id not in payments:
        raise HTTPException(status_code=404, detail="Invoice not found")
    return payments[invoice_id]

@router.post("/")
def create_payment(payment: Payment):
    if payment.invoice_id in payments:
        raise HTTPException(status_code=400, detail="Invoice already exists")
    payments[payment.invoice_id] = payment
    return payment

@router.put("/{invoice_id}")
def update_payment(invoice_id: str, payment: Payment):
    if invoice_id not in payments:
        raise HTTPException(status_code=404, detail="Invoice not found")
    if invoice_id != payment.invoice_id:
        raise HTTPException(status_code=400, detail="Invoice ID mismatch")
    payments[invoice_id] = payment
    return payment

@router.delete("/{invoice_id}")
def delete_payment(invoice_id: str):
    if invoice_id not in payments:
        raise HTTPException(status_code=404, detail="Invoice not found")
    del payments[invoice_id]
    return {"message": "Invoice deleted successfully"}
