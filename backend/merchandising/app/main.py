
from fastapi import FastAPI
from app.routes.products import router as products_router

# Création de l'application FastAPI
app = FastAPI(
    title="Merchandising Service",
    description="API for managing cosmetic products",
    version="1.0.0"
)

# Connexion des routes Products
app.include_router(
    products_router,
    prefix="/api/products",
    tags=["Products"]
)

# Route principale
@app.get("/")
def home():
    return {
        "message": "Merchandising Service is running"
    }
