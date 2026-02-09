"""Schemas Pydantic para Reservation."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Optional

from pydantic import BaseModel, ConfigDict, field_validator

from enums import ReservationStatus

if TYPE_CHECKING:
    from schemas.bag import BagResponse
    from schemas.equipment import EquipmentResponse
    from schemas.event import EventResponse
    from schemas.user import UserResponse


class ReservationBase(BaseModel):
    """Base reservation schema."""

    equipment_id: Optional[str] = None
    bag_id: Optional[str] = None
    event_id: str
    start_date: datetime
    end_date: datetime

    @field_validator("bag_id")
    @classmethod
    def validate_equipment_or_bag(cls, v, info):
        """Validate that exactly one of equipment_id or bag_id is provided."""
        equipment_id = info.data.get("equipment_id")
        if (equipment_id is None and v is None) or (equipment_id is not None and v is not None):
            raise ValueError("Exactly one of equipment_id or bag_id must be provided")
        return v

    @field_validator("end_date")
    @classmethod
    def validate_dates(cls, v, info):
        """Validate that end_date is >= start_date."""
        if "start_date" in info.data and v < info.data["start_date"]:
            raise ValueError("end_date must be greater than or equal to start_date")
        return v


class ReservationCreate(ReservationBase):
    """Schema for creating a reservation."""

    reserved_by: str
    status: ReservationStatus = ReservationStatus.ACTIVE


class ReservationUpdate(BaseModel):
    """Schema for updating a reservation."""

    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    status: Optional[ReservationStatus] = None

    @field_validator("end_date")
    @classmethod
    def validate_dates(cls, v, info):
        """Validate that end_date is >= start_date."""
        if (
            v
            and "start_date" in info.data
            and info.data["start_date"]
            and v < info.data["start_date"]
        ):
            raise ValueError("end_date must be greater than or equal to start_date")
        return v


class ReservationInDB(ReservationBase):
    """Schema for reservation in database."""

    id: str
    reserved_by: str
    status: ReservationStatus
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ReservationResponse(ReservationInDB):
    """Schema for reservation response."""

    pass


class ReservationWithDetails(ReservationInDB):
    """Schema for reservation response with related details."""

    equipment: Optional["EquipmentResponse"] = None
    bag: Optional["BagResponse"] = None
    event: Optional["EventResponse"] = None
    reserved_by_user: Optional["UserResponse"] = None
