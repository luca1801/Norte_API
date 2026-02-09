"""Schemas Pydantic para Bag."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, List, Optional

from pydantic import BaseModel, ConfigDict, Field

from enums import BagStatus

if TYPE_CHECKING:
    from schemas.equipment import EquipmentResponse


class BagBase(BaseModel):
    """Base bag schema."""

    code: str = Field(..., min_length=1, max_length=50)
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None


class BagCreate(BagBase):
    """Schema for creating a bag."""

    status: BagStatus = BagStatus.AVAILABLE


class BagUpdate(BaseModel):
    """Schema for updating a bag."""

    code: Optional[str] = Field(None, min_length=1, max_length=50)
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    status: Optional[BagStatus] = None


class BagInDB(BagBase):
    """Schema for bag in database."""

    id: str
    status: BagStatus
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class BagResponse(BagInDB):
    """Schema for bag response."""

    equipment_count: Optional[int] = None


class BagWithEquipment(BagInDB):
    """Schema for bag response with equipment items."""

    equipment_items: List["EquipmentResponse"] = Field(default_factory=list)
