"""
Modelo de Equipamento para rastreamento de ativos.
"""

import uuid

from sqlalchemy import Column, DateTime, Enum, ForeignKey, String, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from core.database import Base
from enums import EquipmentCondition, EquipmentStatus


class Equipment(Base):
    """Equipment model for asset tracking."""

    __tablename__ = "equipment"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    code = Column(String(50), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    category = Column(String(100), nullable=False, index=True)
    serial = Column(String(100), unique=True, index=True, nullable=True)
    qr_code = Column(String(100), unique=True, index=True, nullable=True)
    status = Column(
        Enum(EquipmentStatus, values_callable=lambda x: [e.value for e in x]), nullable=False, default=EquipmentStatus.AVAILABLE, index=True
    )
    condition = Column(Enum(EquipmentCondition, values_callable=lambda x: [e.value for e in x]), nullable=False, default=EquipmentCondition.GOOD)
    bag_id = Column(
        String(36), ForeignKey("bags.id", ondelete="SET NULL"), index=True, nullable=True
    )
    current_event_id = Column(String(36), ForeignKey("events.id", ondelete="SET NULL"), nullable=True, index=True)
    location = Column(String(255), nullable=True)
    description = Column(Text, nullable=True)
    image = Column(String(500), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # Relationships
    bag = relationship("Bag", back_populates="equipment_items")
    transactions = relationship("Transaction", back_populates="equipment")
    reservations = relationship("Reservation", back_populates="equipment")

    def __repr__(self):
        return (
            f"<Equipment(id={self.id}, code={self.code}, name={self.name}, status={self.status})>"
        )
