"""Schemas Pydantic para Event."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

from enums import EventStatus

if TYPE_CHECKING:
    from schemas.user import UserResponse


class EventBase(BaseModel):
    """Base event schema."""

    code: str = Field(..., min_length=1, max_length=50)
    name: str = Field(..., min_length=1, max_length=255)
    type: str = Field(..., min_length=1, max_length=50)
    category: Optional[str] = Field(None, max_length=100)
    start_date: datetime
    end_date: datetime
    owner_id: Optional[str] = None
    location: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None

    @field_validator("end_date")
    @classmethod
    def validate_dates(cls, v, info):
        """Validate that end_date is >= start_date."""
        if "start_date" in info.data and v < info.data["start_date"]:
            raise ValueError("end_date must be greater than or equal to start_date")
        return v


class EventCreate(EventBase):
    """Schema for creating an event."""

    status: EventStatus = EventStatus.PLANNED


class EventUpdate(BaseModel):
    """Schema for updating an event."""

    code: Optional[str] = Field(None, min_length=1, max_length=50)
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    type: Optional[str] = Field(None, min_length=1, max_length=50)
    category: Optional[str] = Field(None, max_length=100)
    status: Optional[EventStatus] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    owner_id: Optional[str] = None
    location: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None

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


class EventInDB(EventBase):
    """Schema for event in database."""

    id: str
    status: EventStatus
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class EventResponse(EventInDB):
    """Schema for event response."""

    color: Optional[str] = None


class EventWithOwner(EventInDB):
    """Schema for event response with owner details."""

    owner: Optional["UserResponse"] = None
