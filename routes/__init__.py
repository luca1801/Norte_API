"""
Routes package initialization.
Exporta todos os routers do sistema.
"""

from routes.auth import router as auth_router
from routes.bags import router as bags_router
from routes.equipment import router as equipment_router
from routes.events import router as events_router
from routes.reports import router as reports_router
from routes.reservations import router as reservations_router
from routes.transactions import router as transactions_router
from routes.users import router as users_router

__all__ = [
    "auth_router",
    "users_router",
    "equipment_router",
    "bags_router",
    "events_router",
    "transactions_router",
    "reservations_router",
    "reports_router",
]
