"""
Modelo de Transação para rastrear retiradas e devoluções de equipamentos.
"""

import uuid

from sqlalchemy import CheckConstraint, Column, DateTime, Enum, ForeignKey, String, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from core.database import Base
from enums import TransactionStatus, TransactionType


class Transaction(Base):
    """Transaction model for tracking equipment withdrawals and returns."""

    __tablename__ = "transactions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    equipment_id = Column(
        String(36), ForeignKey("equipment.id", ondelete="RESTRICT"), index=True, nullable=True
    )
    bag_id = Column(
        String(36), ForeignKey("bags.id", ondelete="RESTRICT"), index=True, nullable=True
    )
    event_id = Column(
        String(36), ForeignKey("events.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    user_id = Column(
        String(36), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    transaction_type = Column(Enum(TransactionType), nullable=False, index=True)
    status = Column(
        Enum(TransactionStatus), nullable=False, default=TransactionStatus.PENDING, index=True
    )
    scheduled_date = Column(DateTime(timezone=True), nullable=False, index=True)
    actual_date = Column(DateTime(timezone=True), nullable=True, index=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # Relationships
    equipment = relationship("Equipment", back_populates="transactions")
    bag = relationship("Bag", back_populates="transactions")
    event = relationship("Event", back_populates="transactions")
    user = relationship("User", back_populates="transactions")

    # Constraints - Either equipment_id OR bag_id must be set, not both
    __table_args__ = (
        CheckConstraint(
            "(equipment_id IS NOT NULL AND bag_id IS NULL) OR (equipment_id IS NULL AND bag_id IS NOT NULL)",
            name="check_equipment_or_bag",
        ),
    )

    def __repr__(self):
        return f"<Transaction(id={self.id}, type={self.transaction_type}, status={self.status})>"
