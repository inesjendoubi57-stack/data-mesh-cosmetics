
from contextlib import asynccontextmanager

from fastapi import FastAPI
from app.database import initialize_database
from app.routes.products import router as products_router


@asynccontextmanager
async def lifespan(_: FastAPI):
    initialize_database()
    yield


# Création de l'application FastAPI
app = FastAPI(
    title="Merchandising Service",
    description="API for managing cosmetic products",
    version="1.0.0",
    lifespan=lifespan,
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
