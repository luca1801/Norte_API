from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from core.config import settings
from core.database import init_db
from core.logger import get_logger
from routes import auth, bags, equipment, events, reports, reservations, transactions, users

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown events."""
    # Startup
    logger.info("Starting API...")
    init_db()
    logger.info("Database initialized")
    yield
    # Shutdown
    logger.info("Shutting down API...")


# Create FastAPI application
app = FastAPI(
    title=settings.API_TITLE,
    version=settings.API_VERSION,
    description=settings.API_DESCRIPTION,
    lifespan=lifespan,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(equipment.router)
app.include_router(bags.router)
app.include_router(events.router)
app.include_router(transactions.router)
app.include_router(reservations.router)
app.include_router(reports.router)

# Rebuild Pydantic models for specific schemas that reference each other
from importlib import import_module

# Ensure cross-module symbols exist in module globals so Pydantic can resolve forward refs
_schemas_bag = import_module("schemas.bag")
_schemas_equipment = import_module("schemas.equipment")
_schemas_reservation = import_module("schemas.reservation")
_schemas_transaction = import_module("schemas.transaction")
_schemas_event = import_module("schemas.event")

setattr(_schemas_bag, "EquipmentResponse", getattr(_schemas_equipment, "EquipmentResponse"))
setattr(_schemas_equipment, "BagResponse", getattr(_schemas_bag, "BagResponse", None))
setattr(
    _schemas_reservation,
    "EquipmentResponse",
    getattr(_schemas_equipment, "EquipmentResponse", None),
)
setattr(_schemas_reservation, "BagResponse", getattr(_schemas_bag, "BagResponse", None))
setattr(
    _schemas_transaction,
    "EquipmentResponse",
    getattr(_schemas_equipment, "EquipmentResponse", None),
)
setattr(_schemas_transaction, "BagResponse", getattr(_schemas_bag, "BagResponse", None))
setattr(
    _schemas_event, "UserResponse", getattr(import_module("schemas.user"), "UserResponse", None)
)
setattr(_schemas_reservation, "EventResponse", getattr(_schemas_event, "EventResponse", None))
setattr(_schemas_transaction, "EventResponse", getattr(_schemas_event, "EventResponse", None))
setattr(
    _schemas_transaction,
    "UserResponse",
    getattr(import_module("schemas.user"), "UserResponse", None),
)
setattr(
    _schemas_reservation,
    "UserResponse",
    getattr(import_module("schemas.user"), "UserResponse", None),
)

# Rebuild only the models that include forward refs
_schemas_bag.BagWithEquipment.model_rebuild()
_schemas_equipment.EquipmentWithBag.model_rebuild()
_schemas_reservation.ReservationWithDetails.model_rebuild()
_schemas_transaction.TransactionWithDetails.model_rebuild()
_schemas_event.EventWithOwner.model_rebuild()


@app.get("/", tags=["Root"])
def read_root():
    """Root endpoint."""
    return {
        "message": f"Welcome to {settings.API_TITLE}",
        "version": settings.API_VERSION,
        "docs": "/docs",
    }


@app.get("/health", tags=["Health"])
def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=True,
        log_level=settings.LOG_LEVEL.lower(),
    )
