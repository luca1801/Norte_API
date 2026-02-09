"""
Modelo de Bag para agrupar equipamentos.
"""

import uuid

from sqlalchemy import Boolean, Column, DateTime, Enum, String, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from core.database import Base
from enums import BagStatus


class Bag(Base):
    """Bag model for grouping equipment items."""

    __tablename__ = "bags"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    code = Column(String(50), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(
        Enum(BagStatus, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        default=BagStatus.AVAILABLE,
        index=True,
    )
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # Relationships
    equipment_items = relationship("Equipment", back_populates="bag")
    transactions = relationship("Transaction", back_populates="bag")
    reservations = relationship("Reservation", back_populates="bag")

    def __repr__(self):
        return f"<Bag(id={self.id}, code={self.code}, name={self.name}, status={self.status})>"
