from datetime import datetime
from typing import List, Optional, Union
from uuid import UUID

from sqlalchemy import and_, or_
from sqlalchemy.orm import Session

from enums import ReservationStatus
from models.reservation import Reservation
from repositories.base import BaseRepository


class ReservationRepository(BaseRepository[Reservation]):
    def __init__(self, db: Session):
        super().__init__(Reservation, db)

    def list_with_filters(
        self,
        skip: int = 0,
        limit: int = 100,
        status: Optional[ReservationStatus] = None,
        event_id: Optional[Union[str, UUID]] = None,
    ) -> List[Reservation]:
        query = self.db.query(Reservation)
        if status:
            query = query.filter(Reservation.status == status)
        if event_id:
            query = query.filter(Reservation.event_id == event_id)
        return query.order_by(Reservation.start_date.desc()).offset(skip).limit(limit).all()

    def check_conflict(
        self,
        equipment_id: Optional[Union[str, UUID]],
        bag_id: Optional[Union[str, UUID]],
        start_date: datetime,
        end_date: datetime,
        exclude_reservation_id: Optional[Union[str, UUID]] = None,
    ) -> bool:
        query = self.db.query(Reservation).filter(
            Reservation.status == ReservationStatus.ACTIVE,
            or_(
                and_(Reservation.equipment_id == equipment_id, equipment_id is not None),
                and_(Reservation.bag_id == bag_id, bag_id is not None),
            ),
            Reservation.start_date < end_date,
            Reservation.end_date > start_date,
        )

        if exclude_reservation_id:
            query = query.filter(Reservation.id != exclude_reservation_id)

        return query.first() is not None

    def list_active_by_equipment(self, equipment_id: Union[str, UUID]) -> List[Reservation]:
        return (
            self.db.query(Reservation)
            .filter(
                Reservation.equipment_id == equipment_id,
                Reservation.status == ReservationStatus.ACTIVE,
            )
            .all()
        )

    def list_active_by_bag(self, bag_id: Union[str, UUID]) -> List[Reservation]:
        return (
            self.db.query(Reservation)
            .filter(
                Reservation.bag_id == bag_id,
                Reservation.status == ReservationStatus.ACTIVE,
            )
            .all()
        )
