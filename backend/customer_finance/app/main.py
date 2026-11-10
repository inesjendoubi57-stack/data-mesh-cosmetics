
from fastapi import FastAPI
from app.routes.payments import router as payments_router

# Création de l'application FastAPI
app = FastAPI(
    title="Customer Finance Service",
    description="API for managing customer payments",
    version="1.0.0"
)

# Connexion des routes Payments
app.include_router(
    payments_router,
    prefix="/api/payments",
    tags=["Payments"]
)

# Route principale
@app.get("/")
def home():
    return {
        "message": "Customer Finance Service is running"
    }
