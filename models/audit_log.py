"""
Modelo de Log de Auditoria para trilha de auditoria.
"""

import uuid

from sqlalchemy import Column, DateTime, Enum, ForeignKey, String, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from core.database import Base
from enums import AuditAction


class AuditLog(Base):
    """AuditLog model for tracking all changes in the system."""

    __tablename__ = "audit_log"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    table_name = Column(String(50), nullable=False, index=True)
    record_id = Column(String(36), nullable=False, index=True)
    action = Column(Enum(AuditAction), nullable=False)
    old_values = Column(Text, nullable=True)  # JSON string for SQLite compatibility
    new_values = Column(Text, nullable=True)  # JSON string for SQLite compatibility
    user_id = Column(
        String(36), ForeignKey("users.id", ondelete="SET NULL"), index=True, nullable=True
    )
    ip_address = Column(String(45), nullable=True)  # IPv6 support
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )

    # Relationships
    user = relationship("User", back_populates="audit_logs")

    def __repr__(self):
        return f"<AuditLog(id={self.id}, table={self.table_name}, action={self.action})>"
