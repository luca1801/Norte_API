"""
Modelo de Reserva para reservar equipamentos/bags para eventos.
"""

import uuid

from sqlalchemy import CheckConstraint, Column, DateTime, Enum, ForeignKey, String
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from core.database import Base
from enums import ReservationStatus


class Reservation(Base):
    """Reservation model for reserving equipment or bags for events."""

    __tablename__ = "reservations"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    equipment_id = Column(
        String(36), ForeignKey("equipment.id", ondelete="CASCADE"), index=True, nullable=True
    )
    bag_id = Column(
        String(36), ForeignKey("bags.id", ondelete="CASCADE"), index=True, nullable=True
    )
    event_id = Column(
        String(36), ForeignKey("events.id", ondelete="CASCADE"), nullable=False, index=True
    )
    reserved_by = Column(
        String(36), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    start_date = Column(DateTime(timezone=True), nullable=False, index=True)
    end_date = Column(DateTime(timezone=True), nullable=False, index=True)
    status = Column(
        Enum(ReservationStatus), nullable=False, default=ReservationStatus.ACTIVE, index=True
    )
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # Relationships
    equipment = relationship("Equipment", back_populates="reservations")
    bag = relationship("Bag", back_populates="reservations")
    event = relationship("Event", back_populates="reservations")
    reserved_by_user = relationship("User", back_populates="reservations")

    # Constraints
    __table_args__ = (
        CheckConstraint("end_date >= start_date", name="check_reservation_dates"),
        CheckConstraint(
            "(equipment_id IS NOT NULL AND bag_id IS NULL) OR (equipment_id IS NULL AND bag_id IS NOT NULL)",
            name="check_equipment_or_bag_reservation",
        ),
    )

    def __repr__(self):
        return f"<Reservation(id={self.id}, event_id={self.event_id}, status={self.status})>"
