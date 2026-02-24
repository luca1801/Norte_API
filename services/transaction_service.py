from datetime import timedelta, timezone
from typing import List, Optional

from sqlalchemy.orm import Session

from core.logger import get_logger
from enums import BagStatus, EquipmentCondition, EquipmentStatus, EventStatus, TransactionStatus, TransactionType
from models.bag import Bag
from models.equipment import Equipment
from models.event import Event
from models.transaction import Transaction
from models.user import User
from repositories.bag_repo import BagRepository
from repositories.equipment_repo import EquipmentRepository
from repositories.event_repo import EventRepository
from repositories.transaction_repo import TransactionRepository
from schemas.transaction import TransactionCreate, TransactionUpdate
from services.audit import audit_equipment_status_change, audit_insert, audit_update, model_to_dict
from utils.datetime_utils import now_brasilia

logger = get_logger(__name__)


class TransactionService:
    def __init__(self, db: Session):
        self.db = db
        self.transaction_repo = TransactionRepository(db)
        self.event_repo = EventRepository(db)
        self.equipment_repo = EquipmentRepository(db)
        self.bag_repo = BagRepository(db)

    def list(self, skip: int = 0, limit: int = 100, transaction_type: Optional[TransactionType] = None, status: Optional[TransactionStatus] = None) -> List[Transaction]:
        logger.info(f"Listing transactions with filters: type={transaction_type}, status={status}")
        return self.transaction_repo.list_with_filters(skip, limit, transaction_type, status)

    def get_by_id(self, transaction_id: str) -> Transaction:
        logger.info(f"Fetching transaction ID: {transaction_id}")
        transaction = self.transaction_repo.get_by_id(transaction_id)
        if not transaction:
            logger.warning(f"Transaction not found: {transaction_id}")
            raise ValueError("Transaction not found")
        return transaction

    def create(self, transaction_data: TransactionCreate, current_user: User, client_ip: Optional[str] = None) -> Transaction:
        logger.info(f"User {current_user.username} creating {transaction_data.transaction_type.value} transaction")

        event = self._validate_event(transaction_data.event_id)
        equipment = self._validate_equipment(transaction_data, current_user) if transaction_data.equipment_id else None
        bag = self._validate_bag(transaction_data) if transaction_data.bag_id else None

        transaction_dict = transaction_data.model_dump()
        transaction_dict["user_id"] = current_user.id

        new_transaction = self.transaction_repo.create(transaction_dict)

        if transaction_data.transaction_type in [TransactionType.WITHDRAWAL, TransactionType.RETURN]:
            new_transaction.status = TransactionStatus.COMPLETED

        audit_insert(
            db=self.db,
            model=new_transaction,
            user_id=str(current_user.id),
            ip_address=client_ip,
        )

        if equipment:
            self._handle_equipment_transaction(transaction_data, equipment, current_user, client_ip)

        if bag:
            self._handle_bag_transaction(transaction_data, bag, current_user, client_ip)

        self._handle_event_status_update(transaction_data, event)

        self.transaction_repo.commit()
        self.transaction_repo.refresh(new_transaction)

        logger.info(f"Transaction created successfully: ID {new_transaction.id}")
        return new_transaction

    def _validate_event(self, event_id: str) -> Event:
        event = self.event_repo.get_by_id(event_id)
        if not event:
            raise ValueError("Event not found")
        if event.status not in [EventStatus.PLANNED, EventStatus.CONFIRMED, EventStatus.IN_PROGRESS]:
            raise ValueError("Event must be planned, confirmed or in progress for transactions")
        return event

    def _validate_equipment(self, transaction_data: TransactionCreate, current_user: User) -> Equipment:
        equipment = self.equipment_repo.get_by_id(transaction_data.equipment_id)
        if not equipment:
            raise ValueError("Equipment not found")

        if transaction_data.transaction_type == TransactionType.WITHDRAWAL:
            if equipment.status not in [EquipmentStatus.AVAILABLE, EquipmentStatus.RESERVED]:
                in_use_transaction = self.transaction_repo.get_latest_withdrawal_by_equipment(equipment.id)
                event_name = "outro evento"
                if in_use_transaction and in_use_transaction.event_id:
                    using_event = self.event_repo.get_by_id(in_use_transaction.event_id)
                    if using_event:
                        event_name = f'evento "{using_event.name}"'
                raise ValueError(f"Equipamento ja esta em uso no {event_name}. Status atual: {equipment.status.value}")

        if transaction_data.transaction_type == TransactionType.RETURN:
            if equipment.status != EquipmentStatus.IN_USE:
                raise ValueError("Equipment is not currently in use")

        return equipment

    def _validate_bag(self, transaction_data: TransactionCreate) -> Bag:
        bag = self.bag_repo.get_by_id(transaction_data.bag_id)
        if not bag:
            raise ValueError("Bag not found")

        if transaction_data.transaction_type == TransactionType.WITHDRAWAL:
            if bag.status == BagStatus.IN_USE:
                in_use_transaction = self.transaction_repo.get_latest_withdrawal_by_bag(bag.id)
                event_name = "outro evento"
                if in_use_transaction and in_use_transaction.event_id:
                    using_event = self.event_repo.get_by_id(in_use_transaction.event_id)
                    if using_event:
                        event_name = f'evento "{using_event.name}"'
                raise ValueError(f"Bag ja esta em uso no {event_name}. Status atual: {bag.status.value}")

        return bag

    def _handle_equipment_transaction(self, transaction_data: TransactionCreate, equipment: Equipment, current_user: User, client_ip: Optional[str]) -> None:
        old_status = equipment.status.value
        if transaction_data.transaction_type == TransactionType.WITHDRAWAL:
            equipment.status = EquipmentStatus.IN_USE
            equipment.current_event_id = transaction_data.event_id
        elif transaction_data.transaction_type == TransactionType.RETURN:
            return_condition = getattr(transaction_data, 'return_condition', None) or 'ok'
            
            if return_condition == 'ok':
                equipment.status = EquipmentStatus.AVAILABLE
                equipment.current_event_id = None
            elif return_condition == 'damaged':
                equipment.status = EquipmentStatus.MAINTENANCE
                equipment.condition = EquipmentCondition.DAMAGED
                equipment.current_event_id = None
            elif return_condition == 'maintenance':
                equipment.status = EquipmentStatus.MAINTENANCE
                equipment.current_event_id = None
            elif return_condition == 'lost':
                equipment.status = EquipmentStatus.EXCLUDED
                equipment.current_event_id = None

        audit_equipment_status_change(
            db=self.db,
            equipment=equipment,
            old_status=old_status,
            new_status=equipment.status.value,
            user_id=str(current_user.id),
            ip_address=client_ip,
        )

    def _handle_bag_transaction(self, transaction_data: TransactionCreate, bag: Bag, current_user: User, client_ip: Optional[str]) -> None:
        return_condition = getattr(transaction_data, 'return_condition', None) or 'ok'
        
        if transaction_data.transaction_type == TransactionType.WITHDRAWAL:
            bag.status = BagStatus.IN_USE
            bag.current_event_id = transaction_data.event_id
            for equip in bag.equipment_items:
                if equip.status in [EquipmentStatus.AVAILABLE, EquipmentStatus.RESERVED]:
                    old_equip_status = equip.status.value
                    equip.status = EquipmentStatus.IN_USE
                    equip.current_event_id = transaction_data.event_id
                    audit_equipment_status_change(
                        db=self.db,
                        equipment=equip,
                        old_status=old_equip_status,
                        new_status=equip.status.value,
                        user_id=str(current_user.id),
                        ip_address=client_ip,
                    )
        elif transaction_data.transaction_type == TransactionType.RETURN:
            bag.status = BagStatus.AVAILABLE
            bag.current_event_id = None
            for equip in bag.equipment_items:
                if equip.status in [EquipmentStatus.IN_USE, EquipmentStatus.RESERVED]:
                    old_equip_status = equip.status.value
                    
                    if equip.status == EquipmentStatus.RESERVED:
                        equip.status = EquipmentStatus.RESERVED
                    elif return_condition == 'ok':
                        equip.status = EquipmentStatus.AVAILABLE
                        equip.current_event_id = None
                    elif return_condition == 'damaged':
                        equip.status = EquipmentStatus.MAINTENANCE
                        equip.condition = EquipmentCondition.DAMAGED
                        equip.current_event_id = None
                    elif return_condition == 'maintenance':
                        equip.status = EquipmentStatus.MAINTENANCE
                        equip.current_event_id = None
                    elif return_condition == 'lost':
                        equip.status = EquipmentStatus.EXCLUDED
                        equip.current_event_id = None
                    
                    audit_equipment_status_change(
                        db=self.db,
                        equipment=equip,
                        old_status=old_equip_status,
                        new_status=equip.status.value,
                        user_id=str(current_user.id),
                        ip_address=client_ip,
                    )

    def _handle_event_status_update(self, transaction_data: TransactionCreate, event: Event) -> None:
        if transaction_data.transaction_type == TransactionType.WITHDRAWAL:
            if event.status in [EventStatus.PLANNED, EventStatus.CONFIRMED]:
                old_event_status = event.status.value
                event.status = EventStatus.IN_PROGRESS
                logger.info(f"Event {event.id} status changed from {old_event_status} to IN_PROGRESS due to withdrawal")

        elif transaction_data.transaction_type == TransactionType.RETURN:
            event_withdrawals = self.transaction_repo.count_withdrawals_by_event(transaction_data.event_id)
            event_returns = self.transaction_repo.count_returns_by_event(transaction_data.event_id) + 1

            if event_withdrawals > 0 and event_returns >= event_withdrawals:
                if event.status == EventStatus.IN_PROGRESS:
                    current_time = now_brasilia()
                    event_end = event.end_date
                    if event_end.tzinfo is None:
                        event_end = event_end.replace(tzinfo=timezone.utc)

                    if event_end + timedelta(hours=24) <= current_time:
                        event.status = EventStatus.COMPLETED
                        logger.info(f"Event {event.id} status changed to COMPLETED - all items returned ({event_returns}/{event_withdrawals})")

    def update(self, transaction_id: str, transaction_data: TransactionUpdate, current_user: User, client_ip: Optional[str] = None) -> Transaction:
        logger.info(f"User {current_user.username} updating transaction ID: {transaction_id}")

        transaction = self.transaction_repo.get_by_id(transaction_id)
        if not transaction:
            logger.warning(f"Transaction not found: {transaction_id}")
            raise ValueError("Transaction not found")

        old_values = model_to_dict(transaction)

        self.transaction_repo.update(transaction, transaction_data.model_dump(exclude_unset=True))

        if transaction_data.status == TransactionStatus.COMPLETED and not transaction.actual_date:
            transaction.actual_date = now_brasilia()

        audit_update(
            db=self.db,
            model=transaction,
            old_values=old_values,
            user_id=str(current_user.id),
            ip_address=client_ip,
        )

        self.transaction_repo.commit()
        self.transaction_repo.refresh(transaction)

        logger.info(f"Transaction updated successfully: ID {transaction.id}")
        return transaction

    def cancel(self, transaction_id: str, current_user: User, client_ip: Optional[str] = None) -> None:
        logger.info(f"User {current_user.username} cancelling transaction ID: {transaction_id}")

        transaction = self.transaction_repo.get_by_id(transaction_id)
        if not transaction:
            logger.warning(f"Transaction not found: {transaction_id}")
            raise ValueError("Transaction not found")

        if transaction.status == TransactionStatus.COMPLETED:
            raise ValueError("Cannot cancel a completed transaction")

        old_values = model_to_dict(transaction)
        transaction.status = TransactionStatus.CANCELLED

        audit_update(
            db=self.db,
            model=transaction,
            old_values=old_values,
            user_id=str(current_user.id),
            ip_address=client_ip,
        )

        self.transaction_repo.commit()

        logger.info(f"Transaction cancelled successfully: ID {transaction.id}")
