"""
Modelo de Evento para rastrear eventos que utilizam equipamentos.
"""

import uuid

from sqlalchemy import CheckConstraint, Column, DateTime, Enum, ForeignKey, String, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from core.database import Base
from enums import EventStatus


class Event(Base):
    """Event model for tracking events that use equipment."""

    __tablename__ = "events"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    code = Column(String(50), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    type = Column(String(50), nullable=False)  # concert, conference, wedding, etc.
    category = Column(String(100), nullable=True)
    status = Column(Enum(EventStatus), nullable=False, default=EventStatus.PLANNED, index=True)
    start_date = Column(DateTime(timezone=True), nullable=False, index=True)
    end_date = Column(DateTime(timezone=True), nullable=False, index=True)
    owner_id = Column(
        String(36), ForeignKey("users.id", ondelete="SET NULL"), index=True, nullable=True
    )
    location = Column(String(255), nullable=True)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # Relationships
    owner = relationship("User", back_populates="owned_events", foreign_keys=[owner_id])
    transactions = relationship("Transaction", back_populates="event")
    reservations = relationship("Reservation", back_populates="event")

    # Constraints
    __table_args__ = (CheckConstraint("end_date >= start_date", name="check_event_dates"),)

    @property
    def color(self) -> str:
        """Return color based on event status for calendar display."""
        color_map = {
            EventStatus.PLANNED: "#3b82f6",
            EventStatus.CONFIRMED: "#8b5cf6",
            EventStatus.IN_PROGRESS: "#10b981",
            EventStatus.COMPLETED: "#6b7280",
            EventStatus.CANCELLED: "#ef4444",
        }
        return color_map.get(self.status, "#8b5cf6")

    def __repr__(self):
        return f"<Event(id={self.id}, code={self.code}, name={self.name}, status={self.status})>"
