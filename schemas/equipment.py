"""Schemas Pydantic para Equipment."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Optional

from pydantic import BaseModel, ConfigDict, Field

from enums import EquipmentCondition, EquipmentStatus

if TYPE_CHECKING:
    from schemas.bag import BagResponse


class EquipmentBase(BaseModel):
    """Base equipment schema."""

    code: str = Field(..., min_length=1, max_length=50)
    name: str = Field(..., min_length=1, max_length=255)
    category: str = Field(..., min_length=1, max_length=100)
    serial: Optional[str] = Field(None, max_length=100)
    qr_code: Optional[str] = Field(None, max_length=100)
    condition: EquipmentCondition = EquipmentCondition.GOOD
    bag_id: Optional[str] = None
    location: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    image: Optional[str] = None


class EquipmentCreate(EquipmentBase):
    """Schema for creating equipment."""

    status: EquipmentStatus = EquipmentStatus.AVAILABLE


class EquipmentUpdate(BaseModel):
    """Schema for updating equipment."""

    code: Optional[str] = Field(None, min_length=1, max_length=50)
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    category: Optional[str] = Field(None, min_length=1, max_length=100)
    serial: Optional[str] = Field(None, max_length=100)
    qr_code: Optional[str] = Field(None, max_length=100)
    status: Optional[EquipmentStatus] = None
    condition: Optional[EquipmentCondition] = None
    bag_id: Optional[str] = None
    location: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    image: Optional[str] = None


class EquipmentInDB(EquipmentBase):
    """Schema for equipment in database."""

    id: str
    status: EquipmentStatus
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class EquipmentResponse(EquipmentInDB):
    """Schema for equipment response."""

    pass


class EquipmentWithBag(EquipmentInDB):
    """Schema for equipment response with bag details."""

    bag: Optional["BagResponse"] = None
