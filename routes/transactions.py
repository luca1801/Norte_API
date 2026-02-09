from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.orm import Session
from datetime import timedelta

from core.database import get_db
from core.logger import get_logger
from enums import BagStatus, EquipmentStatus, EventStatus, TransactionStatus, TransactionType
from models.bag import Bag
from models.equipment import Equipment
from models.event import Event
from models.transaction import Transaction
from models.user import User
from schemas.transaction import TransactionCreate, TransactionResponse, TransactionUpdate
from services.audit import audit_insert, audit_update, audit_equipment_status_change, model_to_dict
from utils.auth import get_current_operator_or_above, get_current_user
from utils.datetime_utils import now_brasilia

router = APIRouter(prefix="/transactions", tags=["Transactions"])
logger = get_logger(__name__)


def get_client_ip(request: Request) -> Optional[str]:
    """Obtém o IP do cliente da requisição."""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    if request.client:
        return request.client.host
    return None


@router.get("/", response_model=List[TransactionResponse])
def list_transactions(
    skip: int = 0,
    limit: int = 100,
    transaction_type: Optional[TransactionType] = Query(None, alias="type"),
    transaction_status: Optional[TransactionStatus] = Query(None, alias="status"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List all transactions with optional filters."""
    logger.info(f"User {current_user.username} listing transactions")

    query = db.query(Transaction)

    if transaction_type:
        query = query.filter(Transaction.transaction_type == transaction_type)
    if transaction_status:
        query = query.filter(Transaction.status == transaction_status)

    transactions = query.order_by(Transaction.created_at.desc()).offset(skip).limit(limit).all()
    return transactions


@router.get("/{transaction_id}", response_model=TransactionResponse)
def get_transaction(
    transaction_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get transaction by ID."""
    logger.info(f"User {current_user.username} fetching transaction ID: {transaction_id}")
    transaction = db.query(Transaction).filter(Transaction.id == transaction_id).first()

    if not transaction:
        logger.warning(f"Transaction not found: {transaction_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transaction not found",
        )

    return transaction


@router.post("/", response_model=TransactionResponse, status_code=status.HTTP_201_CREATED)
def create_transaction(
    request: Request,
    transaction_data: TransactionCreate,
    current_user: User = Depends(get_current_operator_or_above),
    db: Session = Depends(get_db),
):
    """Create new transaction (withdrawal or return) - operator or above."""
    logger.info(
        f"User {current_user.username} creating {transaction_data.transaction_type.value} transaction"
    )

    # Validate event exists and is active
    event = db.query(Event).filter(Event.id == transaction_data.event_id).first()
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found",
        )

    # Allow transactions for planned, confirmed, or in_progress events
    if event.status not in [EventStatus.PLANNED, EventStatus.CONFIRMED, EventStatus.IN_PROGRESS]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Event must be planned, confirmed or in progress for transactions",
        )

    # Validate equipment if provided
    if transaction_data.equipment_id:
        equipment = (
            db.query(Equipment).filter(Equipment.id == transaction_data.equipment_id).first()
        )
        if not equipment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Equipment not found",
            )

        # For withdrawal, check if equipment is available
        if transaction_data.transaction_type == TransactionType.WITHDRAWAL:
            if equipment.status not in [EquipmentStatus.AVAILABLE, EquipmentStatus.RESERVED]:
                # Find which event is using this equipment
                in_use_transaction = (
                    db.query(Transaction)
                    .filter(
                        Transaction.equipment_id == equipment.id,
                        Transaction.transaction_type == TransactionType.WITHDRAWAL,
                    )
                    .order_by(Transaction.created_at.desc())
                    .first()
                )
                event_name = "outro evento"
                if in_use_transaction and in_use_transaction.event_id:
                    using_event = (
                        db.query(Event).filter(Event.id == in_use_transaction.event_id).first()
                    )
                    if using_event:
                        event_name = f'evento "{using_event.name}"'

                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Equipamento já está em uso no {event_name}. Status atual: {equipment.status.value}",
                )

        # For return, check if equipment is in use
        if transaction_data.transaction_type == TransactionType.RETURN:
            if equipment.status != EquipmentStatus.IN_USE:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Equipment is not currently in use",
                )

    # Validate bag if provided - check if bag or its equipment are already in use
    if transaction_data.bag_id and transaction_data.transaction_type == TransactionType.WITHDRAWAL:
        bag = db.query(Bag).filter(Bag.id == transaction_data.bag_id).first()
        if bag and bag.status == BagStatus.IN_USE:
            # Find which event is using this bag
            in_use_transaction = (
                db.query(Transaction)
                .filter(
                    Transaction.bag_id == bag.id,
                    Transaction.transaction_type == TransactionType.WITHDRAWAL,
                )
                .order_by(Transaction.created_at.desc())
                .first()
            )
            event_name = "outro evento"
            if in_use_transaction and in_use_transaction.event_id:
                using_event = (
                    db.query(Event).filter(Event.id == in_use_transaction.event_id).first()
                )
                if using_event:
                    event_name = f'evento "{using_event.name}"'

            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Bag já está em uso no {event_name}. Status atual: {bag.status.value}",
            )

    # Create transaction
    transaction_dict = transaction_data.model_dump()
    transaction_dict["user_id"] = current_user.id  # Override user_id with current user

    new_transaction = Transaction(**transaction_dict)
    # If creating a transaction via the operator interface, mark it as completed
    # for immediate actions like withdrawals/returns so frontend reflects actual state.
    try:
        if transaction_data.transaction_type in [
            TransactionType.WITHDRAWAL,
            TransactionType.RETURN,
        ]:
            new_transaction.status = TransactionStatus.COMPLETED
    except Exception:
        # Fallback: keep default status if something goes wrong
        pass

    db.add(new_transaction)
    db.flush()  # Flush to get the ID before commit

    # Get client IP for audit
    client_ip = get_client_ip(request)

    # Audit: Register transaction creation
    audit_insert(
        db=db,
        model=new_transaction,
        user_id=str(current_user.id),
        ip_address=client_ip,
    )

    # Update equipment status if equipment_id is provided
    if transaction_data.equipment_id and equipment:
        old_status = equipment.status.value
        if transaction_data.transaction_type == TransactionType.WITHDRAWAL:
            equipment.status = EquipmentStatus.IN_USE
        elif transaction_data.transaction_type == TransactionType.RETURN:
            equipment.status = EquipmentStatus.AVAILABLE

        # Audit: Register equipment status change
        audit_equipment_status_change(
            db=db,
            equipment=equipment,
            old_status=old_status,
            new_status=equipment.status.value,
            user_id=str(current_user.id),
            ip_address=client_ip,
        )

    # Update bag status if bag_id is provided
    if transaction_data.bag_id:
        bag = db.query(Bag).filter(Bag.id == transaction_data.bag_id).first()
        if bag:
            if transaction_data.transaction_type == TransactionType.WITHDRAWAL:
                bag.status = BagStatus.IN_USE
                # Also update all equipment in the bag
                for equip in bag.equipment_items:
                    if equip.status in [EquipmentStatus.AVAILABLE, EquipmentStatus.RESERVED]:
                        old_equip_status = equip.status.value
                        equip.status = EquipmentStatus.IN_USE
                        # Audit each equipment status change
                        audit_equipment_status_change(
                            db=db,
                            equipment=equip,
                            old_status=old_equip_status,
                            new_status=equip.status.value,
                            user_id=str(current_user.id),
                            ip_address=client_ip,
                        )
            elif transaction_data.transaction_type == TransactionType.RETURN:
                bag.status = BagStatus.AVAILABLE
                # Also update all equipment in the bag
                for equip in bag.equipment_items:
                    if equip.status == EquipmentStatus.IN_USE:
                        old_equip_status = equip.status.value
                        equip.status = EquipmentStatus.AVAILABLE
                        # Audit each equipment status change
                        audit_equipment_status_change(
                            db=db,
                            equipment=equip,
                            old_status=old_equip_status,
                            new_status=equip.status.value,
                            user_id=str(current_user.id),
                            ip_address=client_ip,
                        )

    # Auto-update event status based on transaction type
    if transaction_data.transaction_type == TransactionType.WITHDRAWAL:
        # When any withdrawal happens, set event to IN_PROGRESS
        if event.status in [EventStatus.PLANNED, EventStatus.CONFIRMED]:
            old_event_status = event.status.value
            event.status = EventStatus.IN_PROGRESS
            logger.info(
                f"Event {event.id} status changed from {old_event_status} to IN_PROGRESS due to withdrawal"
            )

    elif transaction_data.transaction_type == TransactionType.RETURN:
        # Check if all withdrawals have been returned
        event_withdrawals = (
            db.query(Transaction)
            .filter(
                Transaction.event_id == transaction_data.event_id,
                Transaction.transaction_type == TransactionType.WITHDRAWAL,
            )
            .count()
        )

        # Count returns including the current one being created
        event_returns = (
            db.query(Transaction)
            .filter(
                Transaction.event_id == transaction_data.event_id,
                Transaction.transaction_type == TransactionType.RETURN,
            )
            .count()
            + 1
        )  # +1 for the current return being created

        # If all items have been returned AND event end_date has passed, mark event as completed
        if event_withdrawals > 0 and event_returns >= event_withdrawals:
            if event.status == EventStatus.IN_PROGRESS:
                # Check if event end_date has passed
                current_time = now_brasilia()
                # Convert event.end_date to timezone-aware if needed
                event_end = event.end_date
                if event_end.tzinfo is None:
                    from datetime import timezone

                    event_end = event_end.replace(tzinfo=timezone.utc)

                if event_end + timedelta(hours=24) <= current_time:
                    event.status = EventStatus.COMPLETED
                    logger.info(
                        f"Event {event.id} status changed to COMPLETED - all items returned ({event_returns}/{event_withdrawals}) and event end_date + 24h passed"
                    )
                else:
                    logger.info(
                        f"Event {event.id} - all items returned ({event_returns}/{event_withdrawals}) but end_date + 24h not passed yet. Status remains IN_PROGRESS"
                    )

    db.commit()
    db.refresh(new_transaction)

    logger.info(f"Transaction created successfully: ID {new_transaction.id}")
    return new_transaction


@router.put("/{transaction_id}", response_model=TransactionResponse)
def update_transaction(
    request: Request,
    transaction_id: str,
    transaction_data: TransactionUpdate,
    current_user: User = Depends(get_current_operator_or_above),
    db: Session = Depends(get_db),
):
    """Update transaction - operator or above."""
    logger.info(f"User {current_user.username} updating transaction ID: {transaction_id}")
    transaction = db.query(Transaction).filter(Transaction.id == transaction_id).first()

    if not transaction:
        logger.warning(f"Transaction not found: {transaction_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transaction not found",
        )

    # Save old values for audit
    old_values = model_to_dict(transaction)

    # Update fields
    for field, value in transaction_data.model_dump(exclude_unset=True).items():
        setattr(transaction, field, value)

    # If status is being set to completed, set actual_date
    if transaction_data.status == TransactionStatus.COMPLETED and not transaction.actual_date:
        transaction.actual_date = now_brasilia()

    # Audit: Register transaction update
    client_ip = get_client_ip(request)
    audit_update(
        db=db,
        model=transaction,
        old_values=old_values,
        user_id=str(current_user.id),
        ip_address=client_ip,
    )

    db.commit()
    db.refresh(transaction)

    logger.info(f"Transaction updated successfully: ID {transaction.id}")
    return transaction


@router.delete("/{transaction_id}", status_code=status.HTTP_204_NO_CONTENT)
def cancel_transaction(
    request: Request,
    transaction_id: str,
    current_user: User = Depends(get_current_operator_or_above),
    db: Session = Depends(get_db),
):
    """Cancel transaction - sets status to CANCELLED."""
    logger.info(f"User {current_user.username} cancelling transaction ID: {transaction_id}")
    transaction = db.query(Transaction).filter(Transaction.id == transaction_id).first()

    if not transaction:
        logger.warning(f"Transaction not found: {transaction_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transaction not found",
        )

    if transaction.status == TransactionStatus.COMPLETED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot cancel a completed transaction",
        )

    # Save old values for audit
    old_values = model_to_dict(transaction)

    transaction.status = TransactionStatus.CANCELLED

    # Audit: Register transaction cancellation
    client_ip = get_client_ip(request)
    audit_update(
        db=db,
        model=transaction,
        old_values=old_values,
        user_id=str(current_user.id),
        ip_address=client_ip,
    )

    db.commit()

    logger.info(f"Transaction cancelled successfully: ID {transaction.id}")
