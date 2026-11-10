
from fastapi import APIRouter, HTTPException
from app.schemas.payment import Payment

router = APIRouter()

# Données temporaires des paiements
payments = {
    1: Payment(
        payment_id=1,
        customer_id=101,
        amount=120.5,
        payment_status="Paid"
    ),
    2: Payment(
        payment_id=2,
        customer_id=102,
        amount=75.0,
        payment_status="Pending"
    )
}

# GET : récupérer tous les paiements
@router.get("/")
def get_payments():
    return list(payments.values())


# GET : récupérer un paiement par ID
@router.get("/{payment_id}")
def get_payment(payment_id: int):
    if payment_id not in payments:
        raise HTTPException(
            status_code=404,
            detail="Payment not found"
        )
    return payments[payment_id]


# POST : ajouter un paiement
@router.post("/")
def add_payment(payment: Payment):
    if payment.payment_id in payments:
        raise HTTPException(
            status_code=400,
            detail="Payment already exists"
        )

    payments[payment.payment_id] = payment

    return {
        "message": "Payment added successfully",
        "payment": payment
    }


# PUT : modifier un paiement
@router.put("/{payment_id}")
def update_payment(payment_id: int, payment: Payment):
    if payment_id not in payments:
        raise HTTPException(
            status_code=404,
            detail="Payment not found"
        )

    if payment.payment_id != payment_id:
        raise HTTPException(
            status_code=400,
            detail="Payment ID mismatch"
        )

    payments[payment_id] = payment

    return {
        "message": "Payment updated successfully",
        "payment": payment
    }


# DELETE : supprimer un paiement
@router.delete("/{payment_id}")
def delete_payment(payment_id: int):
    if payment_id not in payments:
        raise HTTPException(
            status_code=404,
            detail="Payment not found"
        )

    del payments[payment_id]

    return {
        "message": "Payment deleted successfully"
    }
