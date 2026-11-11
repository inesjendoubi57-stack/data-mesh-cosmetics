
from contextlib import asynccontextmanager

from fastapi import FastAPI
from app.database import initialize_database
from app.routes.deliveries import router as deliveries_router


@asynccontextmanager
async def lifespan(_: FastAPI):
    initialize_database()
    yield


# Création de l'application FastAPI
app = FastAPI(
    title="Fulfillment Service",
    description="API for managing deliveries",
    version="1.0.0",
    lifespan=lifespan,
)

# Connexion des routes Deliveries
app.include_router(
    deliveries_router,
    prefix="/api/deliveries",
    tags=["Deliveries"]
)

# Route principale
@app.get("/")
def home():
    return {
        "message": "Fulfillment Service is running"
    }
