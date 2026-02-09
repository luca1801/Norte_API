"""
Schemas Pydantic para AuditLog.
"""

import json
from datetime import datetime
from typing import Any, Dict, Optional

from pydantic import BaseModel, ConfigDict, field_validator

from enums import AuditAction


class AuditLogResponse(BaseModel):
    """Schema for audit log response."""

    id: str
    table_name: str
    record_id: str
    action: AuditAction
    old_values: Optional[Dict[str, Any]] = None
    new_values: Optional[Dict[str, Any]] = None
    user_id: Optional[str] = None
    ip_address: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

    @field_validator("old_values", "new_values", mode="before")
    @classmethod
    def parse_json_string(cls, v):
        """Converte string JSON para dict se necessário."""
        if v is None:
            return None
        if isinstance(v, str):
            try:
                return json.loads(v)
            except json.JSONDecodeError:
                return None
        return v


class AuditLogCreate(BaseModel):
    """Schema for creating an audit log entry."""

    table_name: str
    record_id: str
    action: AuditAction
    old_values: Optional[Dict[str, Any]] = None
    new_values: Optional[Dict[str, Any]] = None
    user_id: Optional[str] = None
    ip_address: Optional[str] = None
