from typing import List, Optional, Union
from uuid import UUID

from sqlalchemy.orm import Session

from enums import TransactionStatus, TransactionType
from models.transaction import Transaction
from repositories.base import BaseRepository


class TransactionRepository(BaseRepository[Transaction]):
    def __init__(self, db: Session):
        super().__init__(Transaction, db)

    def list_with_filters(
        self,
        skip: int = 0,
        limit: int = 100,
        transaction_type: Optional[TransactionType] = None,
        status: Optional[TransactionStatus] = None,
    ) -> List[Transaction]:
        query = self.db.query(Transaction)
        if transaction_type:
            query = query.filter(Transaction.transaction_type == transaction_type)
        if status:
            query = query.filter(Transaction.status == status)
        return query.order_by(Transaction.created_at.desc()).offset(skip).limit(limit).all()

    def get_latest_withdrawal_by_equipment(self, equipment_id: Union[str, UUID]) -> Optional[Transaction]:
        return (
            self.db.query(Transaction)
            .filter(
                Transaction.equipment_id == equipment_id,
                Transaction.transaction_type == TransactionType.WITHDRAWAL,
            )
            .order_by(Transaction.created_at.desc())
            .first()
        )

    def get_latest_withdrawal_by_bag(self, bag_id: Union[str, UUID]) -> Optional[Transaction]:
        return (
            self.db.query(Transaction)
            .filter(
                Transaction.bag_id == bag_id,
                Transaction.transaction_type == TransactionType.WITHDRAWAL,
            )
            .order_by(Transaction.created_at.desc())
            .first()
        )

    def count_withdrawals_by_event(self, event_id: Union[str, UUID]) -> int:
        return (
            self.db.query(Transaction)
            .filter(
                Transaction.event_id == event_id,
                Transaction.transaction_type == TransactionType.WITHDRAWAL,
            )
            .count()
        )

    def count_returns_by_event(self, event_id: Union[str, UUID]) -> int:
        return (
            self.db.query(Transaction)
            .filter(
                Transaction.event_id == event_id,
                Transaction.transaction_type == TransactionType.RETURN,
            )
            .count()
        )
