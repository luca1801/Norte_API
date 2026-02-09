"""
Schemas package initialization.
Exporta todos os schemas Pydantic do sistema.
"""

from schemas.audit_log import AuditLogCreate, AuditLogResponse
from schemas.bag import BagBase, BagCreate, BagInDB, BagResponse, BagUpdate, BagWithEquipment
from schemas.equipment import (
    EquipmentBase,
    EquipmentCreate,
    EquipmentInDB,
    EquipmentResponse,
    EquipmentUpdate,
    EquipmentWithBag,
)
from schemas.event import (
    EventBase,
    EventCreate,
    EventInDB,
    EventResponse,
    EventUpdate,
    EventWithOwner,
)
from schemas.reservation import (
    ReservationBase,
    ReservationCreate,
    ReservationInDB,
    ReservationResponse,
    ReservationUpdate,
    ReservationWithDetails,
)
from schemas.transaction import (
    TransactionBase,
    TransactionCreate,
    TransactionInDB,
    TransactionResponse,
    TransactionUpdate,
    TransactionWithDetails,
)
from schemas.user import (
    Token,
    TokenData,
    UserBase,
    UserCreate,
    UserInDB,
    UserLogin,
    UserResponse,
    UserUpdate,
)

__all__ = [
    # User
    "UserBase",
    "UserCreate",
    "UserUpdate",
    "UserInDB",
    "UserResponse",
    "UserLogin",
    "Token",
    "TokenData",
    # Bag
    "BagBase",
    "BagCreate",
    "BagUpdate",
    "BagInDB",
    "BagResponse",
    "BagWithEquipment",
    # Equipment
    "EquipmentBase",
    "EquipmentCreate",
    "EquipmentUpdate",
    "EquipmentInDB",
    "EquipmentResponse",
    "EquipmentWithBag",
    # Event
    "EventBase",
    "EventCreate",
    "EventUpdate",
    "EventInDB",
    "EventResponse",
    "EventWithOwner",
    # Transaction
    "TransactionBase",
    "TransactionCreate",
    "TransactionUpdate",
    "TransactionInDB",
    "TransactionResponse",
    "TransactionWithDetails",
    # Reservation
    "ReservationBase",
    "ReservationCreate",
    "ReservationUpdate",
    "ReservationInDB",
    "ReservationResponse",
    "ReservationWithDetails",
    # AuditLog
    "AuditLogResponse",
    "AuditLogCreate",
]
