from typing import List, Optional

from sqlalchemy.orm import Session

from core.logger import get_logger
from enums import BagStatus, EquipmentStatus, EventStatus, ReservationStatus
from models.bag import Bag
from models.equipment import Equipment
from models.event import Event
from models.reservation import Reservation
from models.user import User
from repositories.bag_repo import BagRepository
from repositories.equipment_repo import EquipmentRepository
from repositories.event_repo import EventRepository
from repositories.reservation_repo import ReservationRepository
from schemas.reservation import ReservationCreate, ReservationUpdate

logger = get_logger(__name__)


class ReservationService:
    def __init__(self, db: Session):
        self.db = db
        self.reservation_repo = ReservationRepository(db)
        self.event_repo = EventRepository(db)
        self.equipment_repo = EquipmentRepository(db)
        self.bag_repo = BagRepository(db)

    def list(self, skip: int = 0, limit: int = 100, status: Optional[ReservationStatus] = None, event_id: Optional[str] = None) -> List[Reservation]:
        logger.info(f"Listing reservations with filters: status={status}, event_id={event_id}")
        return self.reservation_repo.list_with_filters(skip, limit, status, event_id)

    def get_by_id(self, reservation_id: str) -> Reservation:
        logger.info(f"Fetching reservation ID: {reservation_id}")
        reservation = self.reservation_repo.get_by_id(reservation_id)
        if not reservation:
            logger.warning(f"Reservation not found: {reservation_id}")
            raise ValueError("Reservation not found")
        return reservation

    def create(self, reservation_data: ReservationCreate, current_user: User) -> Reservation:
        logger.info(f"User {current_user.username} creating reservation")

        event = self._validate_event(reservation_data.event_id)
        equipment = self._validate_equipment(reservation_data) if reservation_data.equipment_id else None
        bag = self._validate_bag(reservation_data) if reservation_data.bag_id else None

        if self.reservation_repo.check_conflict(
            reservation_data.equipment_id,
            reservation_data.bag_id,
            reservation_data.start_date,
            reservation_data.end_date,
        ):
            raise ValueError("Conflicting reservation exists for the specified dates")

        reservation_dict = reservation_data.model_dump()
        reservation_dict["reserved_by"] = current_user.id

        new_reservation = self.reservation_repo.create(reservation_dict)

        if equipment:
            equipment.status = EquipmentStatus.RESERVED
            equipment.current_event_id = reservation_data.event_id
        if bag:
            bag.status = BagStatus.RESERVED
            bag.current_event_id = reservation_data.event_id
            bag_equipment = self.equipment_repo.list_by_bag(bag.id)
            for eq in bag_equipment:
                eq.status = EquipmentStatus.RESERVED
                eq.current_event_id = reservation_data.event_id

        self.reservation_repo.commit()
        self.reservation_repo.refresh(new_reservation)

        logger.info(f"Reservation created successfully: ID {new_reservation.id}")
        return new_reservation

    def _validate_event(self, event_id: str) -> Event:
        event = self.event_repo.get_by_id(event_id)
        if not event:
            raise ValueError("Event not found")
        if event.status not in [EventStatus.CONFIRMED, EventStatus.IN_PROGRESS]:
            raise ValueError(f"Reservas so podem ser feitas para eventos confirmados ou em andamento (status atual: {event.status.value})")
        return event

    def _validate_equipment(self, reservation_data: ReservationCreate) -> Equipment:
        equipment = self.equipment_repo.get_by_id(reservation_data.equipment_id)
        if not equipment:
            raise ValueError("Equipment not found")

        if equipment.bag_id:
            raise ValueError("Equipamento pertence a uma bag e nao pode ser reservado individualmente. Reserve a bag completa.")

        if equipment.status != EquipmentStatus.AVAILABLE:
            raise ValueError(f"Equipment is not available for reservation (current status: {equipment.status.value})")

        return equipment

    def _validate_bag(self, reservation_data: ReservationCreate) -> Bag:
        bag = self.bag_repo.get_by_id(reservation_data.bag_id)
        if not bag:
            raise ValueError("Bag not found")

        if not bag.is_active:
            raise ValueError("Bag is not active")

        if bag.status != BagStatus.AVAILABLE:
            raise ValueError(f"Bag is not available for reservation (current status: {bag.status.value})")

        return bag

    def update(self, reservation_id: str, reservation_data: ReservationUpdate) -> Reservation:
        logger.info(f"Updating reservation ID: {reservation_id}")

        reservation = self.reservation_repo.get_by_id(reservation_id)
        if not reservation:
            logger.warning(f"Reservation not found: {reservation_id}")
            raise ValueError("Reservation not found")

        new_start = reservation_data.start_date or reservation.start_date
        new_end = reservation_data.end_date or reservation.end_date

        if reservation_data.start_date or reservation_data.end_date:
            if self.reservation_repo.check_conflict(
                reservation.equipment_id,
                reservation.bag_id,
                new_start,
                new_end,
                exclude_reservation_id=reservation_id,
            ):
                raise ValueError("Conflicting reservation exists for the specified dates")

        self.reservation_repo.update(reservation, reservation_data.model_dump(exclude_unset=True))

        if reservation_data.status in [ReservationStatus.CANCELLED, ReservationStatus.COMPLETED]:
            self._release_equipment_and_bag(reservation)

        self.reservation_repo.commit()
        self.reservation_repo.refresh(reservation)

        logger.info(f"Reservation updated successfully: ID {reservation.id}")
        return reservation

    def _release_equipment_and_bag(self, reservation: Reservation) -> None:
        if reservation.equipment_id:
            equipment = self.equipment_repo.get_by_id(reservation.equipment_id)
            if equipment:
                equipment.status = EquipmentStatus.AVAILABLE
                equipment.current_event_id = None

        if reservation.bag_id:
            bag = self.bag_repo.get_by_id(reservation.bag_id)
            if bag:
                bag.status = BagStatus.AVAILABLE
                bag.current_event_id = None
                bag_equipment = self.equipment_repo.list_by_bag(bag.id)
                for eq in bag_equipment:
                    eq.status = EquipmentStatus.AVAILABLE
                    eq.current_event_id = None

    def cancel(self, reservation_id: str) -> None:
        logger.info(f"Cancelling reservation ID: {reservation_id}")

        reservation = self.reservation_repo.get_by_id(reservation_id)
        if not reservation:
            logger.warning(f"Reservation not found: {reservation_id}")
            raise ValueError("Reservation not found")

        if reservation.status != ReservationStatus.ACTIVE:
            raise ValueError("Only active reservations can be cancelled")

        reservation.status = ReservationStatus.CANCELLED
        self._release_equipment_and_bag(reservation)

        self.reservation_repo.commit()

        logger.info(f"Reservation cancelled successfully: ID {reservation.id}")
