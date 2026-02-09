"""Schemas Pydantic para Transaction."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Optional

from pydantic import BaseModel, ConfigDict, field_validator

from enums import TransactionStatus, TransactionType

if TYPE_CHECKING:
    from schemas.bag import BagResponse
    from schemas.equipment import EquipmentResponse
    from schemas.event import EventResponse
    from schemas.user import UserResponse


class TransactionBase(BaseModel):
    """Base transaction schema."""

    equipment_id: Optional[str] = None
    bag_id: Optional[str] = None
    event_id: str
    transaction_type: TransactionType
    scheduled_date: datetime
    notes: Optional[str] = None

    @field_validator("bag_id")
    @classmethod
    def validate_equipment_or_bag(cls, v, info):
        """Validate that exactly one of equipment_id or bag_id is provided."""
        equipment_id = info.data.get("equipment_id")
        if (equipment_id is None and v is None) or (equipment_id is not None and v is not None):
            raise ValueError("Exactly one of equipment_id or bag_id must be provided")
        return v


class TransactionCreate(TransactionBase):
    """Schema for creating a transaction."""

    status: TransactionStatus = TransactionStatus.PENDING
    user_id: str


class TransactionUpdate(BaseModel):
    """Schema for updating a transaction."""

    status: Optional[TransactionStatus] = None
    scheduled_date: Optional[datetime] = None
    actual_date: Optional[datetime] = None
    notes: Optional[str] = None


class TransactionInDB(TransactionBase):
    """Schema for transaction in database."""

    id: str
    user_id: str
    status: TransactionStatus
    actual_date: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TransactionResponse(TransactionInDB):
    """Schema for transaction response."""

    pass


class TransactionWithDetails(TransactionInDB):
    """Schema for transaction response with related details."""

    equipment: Optional["EquipmentResponse"] = None
    bag: Optional["BagResponse"] = None
    event: Optional["EventResponse"] = None
    user: Optional["UserResponse"] = None
