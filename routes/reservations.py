"""
Routes for Reservation management.
"""

from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import and_, or_
from sqlalchemy.orm import Session

from core.database import get_db
from core.logger import get_logger
from enums import BagStatus, EquipmentStatus, EventStatus, ReservationStatus
from models.bag import Bag
from models.equipment import Equipment
from models.event import Event
from models.reservation import Reservation
from models.user import User
from schemas.reservation import ReservationCreate, ReservationResponse, ReservationUpdate
from utils.auth import get_current_manager_or_admin, get_current_user

router = APIRouter(prefix="/reservations", tags=["Reservations"])
logger = get_logger(__name__)


def check_reservation_conflict(
    db: Session,
    equipment_id: Optional[str],
    bag_id: Optional[str],
    start_date: datetime,
    end_date: datetime,
    exclude_reservation_id: Optional[str] = None,
) -> bool:
    """Check if there's a conflicting reservation for the equipment or bag."""
    query = db.query(Reservation).filter(
        Reservation.status == ReservationStatus.ACTIVE,
        or_(
            and_(Reservation.equipment_id == equipment_id, equipment_id is not None),
            and_(Reservation.bag_id == bag_id, bag_id is not None),
        ),
        # Check for overlapping dates
        Reservation.start_date < end_date,
        Reservation.end_date > start_date,
    )

    if exclude_reservation_id:
        query = query.filter(Reservation.id != exclude_reservation_id)

    return query.first() is not None


@router.get("/", response_model=List[ReservationResponse])
def list_reservations(
    skip: int = 0,
    limit: int = 100,
    reservation_status: Optional[ReservationStatus] = Query(None, alias="status"),
    event_id: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List all reservations with optional filters."""
    logger.info(f"User {current_user.username} listing reservations")

    query = db.query(Reservation)

    if reservation_status:
        query = query.filter(Reservation.status == reservation_status)
    if event_id:
        query = query.filter(Reservation.event_id == event_id)

    reservations = query.order_by(Reservation.start_date.desc()).offset(skip).limit(limit).all()
    return reservations


@router.get("/{reservation_id}", response_model=ReservationResponse)
def get_reservation(
    reservation_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get reservation by ID."""
    logger.info(f"User {current_user.username} fetching reservation ID: {reservation_id}")
    reservation = db.query(Reservation).filter(Reservation.id == reservation_id).first()

    if not reservation:
        logger.warning(f"Reservation not found: {reservation_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reservation not found",
        )

    return reservation


@router.post("/", response_model=ReservationResponse, status_code=status.HTTP_201_CREATED)
def create_reservation(
    reservation_data: ReservationCreate,
    current_user: User = Depends(get_current_manager_or_admin),
    db: Session = Depends(get_db),
):
    """Create new reservation (manager or admin only)."""
    logger.info(f"User {current_user.username} creating reservation")

    # Validate event exists
    event = db.query(Event).filter(Event.id == reservation_data.event_id).first()
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found",
        )

    # RN: Event must be confirmed or in_progress to accept reservations
    if event.status not in [EventStatus.CONFIRMED, EventStatus.IN_PROGRESS]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Reservas só podem ser feitas para eventos confirmados ou em andamento (status atual: {event.status.value})",
        )

    # Validate equipment or bag exists
    if reservation_data.equipment_id:
        equipment = (
            db.query(Equipment).filter(Equipment.id == reservation_data.equipment_id).first()
        )
        if not equipment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Equipment not found",
            )

        # RN: Equipment belonging to a bag cannot be reserved individually
        if equipment.bag_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Equipamento pertence a uma bag e não pode ser reservado individualmente. Reserve a bag completa.",
            )

        # Check if equipment is available
        if equipment.status not in [EquipmentStatus.AVAILABLE]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Equipment is not available for reservation (current status: {equipment.status.value})",
            )

    if reservation_data.bag_id:
        bag = db.query(Bag).filter(Bag.id == reservation_data.bag_id).first()
        if not bag:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Bag not found",
            )

        if not bag.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Bag is not active",
            )

        # Check if bag is available
        if bag.status not in [BagStatus.AVAILABLE]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Bag is not available for reservation (current status: {bag.status.value})",
            )

    # Check for conflicting reservations
    if check_reservation_conflict(
        db,
        reservation_data.equipment_id,
        reservation_data.bag_id,
        reservation_data.start_date,
        reservation_data.end_date,
    ):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Conflicting reservation exists for the specified dates",
        )

    # Create reservation
    reservation_dict = reservation_data.model_dump()
    reservation_dict["reserved_by"] = current_user.id  # Override reserved_by with current user

    new_reservation = Reservation(**reservation_dict)
    db.add(new_reservation)

    # Update equipment/bag status to reserved
    if reservation_data.equipment_id and equipment:
        equipment.status = EquipmentStatus.RESERVED
    if reservation_data.bag_id and bag:
        bag.status = BagStatus.RESERVED
        # Also reserve all equipment inside this bag
        bag_equipment = db.query(Equipment).filter(Equipment.bag_id == bag.id).all()
        for eq in bag_equipment:
            eq.status = EquipmentStatus.RESERVED

    db.commit()
    db.refresh(new_reservation)

    logger.info(f"Reservation created successfully: ID {new_reservation.id}")
    return new_reservation


@router.put("/{reservation_id}", response_model=ReservationResponse)
def update_reservation(
    reservation_id: str,
    reservation_data: ReservationUpdate,
    current_user: User = Depends(get_current_manager_or_admin),
    db: Session = Depends(get_db),
):
    """Update reservation (manager or admin only)."""
    logger.info(f"User {current_user.username} updating reservation ID: {reservation_id}")
    reservation = db.query(Reservation).filter(Reservation.id == reservation_id).first()

    if not reservation:
        logger.warning(f"Reservation not found: {reservation_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reservation not found",
        )

    # Check for date conflicts if dates are being updated
    new_start = reservation_data.start_date or reservation.start_date
    new_end = reservation_data.end_date or reservation.end_date

    if reservation_data.start_date or reservation_data.end_date:
        if check_reservation_conflict(
            db,
            reservation.equipment_id,
            reservation.bag_id,
            new_start,
            new_end,
            exclude_reservation_id=reservation_id,
        ):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Conflicting reservation exists for the specified dates",
            )

    # Update fields
    for field, value in reservation_data.model_dump(exclude_unset=True).items():
        setattr(reservation, field, value)

    # If status is being set to cancelled or completed, update equipment/bag status
    if reservation_data.status in [ReservationStatus.CANCELLED, ReservationStatus.COMPLETED]:
        if reservation.equipment_id:
            equipment = db.query(Equipment).filter(Equipment.id == reservation.equipment_id).first()
            if equipment:
                equipment.status = EquipmentStatus.AVAILABLE
        if reservation.bag_id:
            bag = db.query(Bag).filter(Bag.id == reservation.bag_id).first()
            if bag:
                bag.status = BagStatus.AVAILABLE
                # Also release all equipment inside this bag
                bag_equipment = db.query(Equipment).filter(Equipment.bag_id == bag.id).all()
                for eq in bag_equipment:
                    eq.status = EquipmentStatus.AVAILABLE

    db.commit()
    db.refresh(reservation)

    logger.info(f"Reservation updated successfully: ID {reservation.id}")
    return reservation


@router.delete("/{reservation_id}", status_code=status.HTTP_204_NO_CONTENT)
def cancel_reservation(
    reservation_id: str,
    current_user: User = Depends(get_current_manager_or_admin),
    db: Session = Depends(get_db),
):
    """Cancel reservation (manager or admin only) - Sets status to CANCELLED."""
    logger.info(f"User {current_user.username} cancelling reservation ID: {reservation_id}")
    reservation = db.query(Reservation).filter(Reservation.id == reservation_id).first()

    if not reservation:
        logger.warning(f"Reservation not found: {reservation_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reservation not found",
        )

    if reservation.status != ReservationStatus.ACTIVE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only active reservations can be cancelled",
        )

    # Cancel reservation
    reservation.status = ReservationStatus.CANCELLED

    # Update equipment/bag status back to available
    if reservation.equipment_id:
        equipment = db.query(Equipment).filter(Equipment.id == reservation.equipment_id).first()
        if equipment:
            equipment.status = EquipmentStatus.AVAILABLE
    if reservation.bag_id:
        bag = db.query(Bag).filter(Bag.id == reservation.bag_id).first()
        if bag:
            bag.status = BagStatus.AVAILABLE
            # Also release all equipment inside this bag
            bag_equipment = db.query(Equipment).filter(Equipment.bag_id == bag.id).all()
            for eq in bag_equipment:
                eq.status = EquipmentStatus.AVAILABLE

    db.commit()

    logger.info(f"Reservation cancelled successfully: ID {reservation.id}")
