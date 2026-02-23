from typing import List, Optional, Union
from uuid import UUID

from sqlalchemy.orm import Session

from enums import EventStatus
from models.event import Event
from repositories.base import BaseRepository


class EventRepository(BaseRepository[Event]):
    def __init__(self, db: Session):
        super().__init__(Event, db)

    def get_by_code(self, code: str) -> Optional[Event]:
        return self.db.query(Event).filter(Event.code == code).first()

    def exists_by_code(self, code: str) -> bool:
        return self.db.query(Event).filter(Event.code == code).first() is not None

    def list_by_status(
        self, status: EventStatus, skip: int = 0, limit: int = 100
    ) -> List[Event]:
        return (
            self.db.query(Event)
            .filter(Event.status == status)
            .offset(skip)
            .limit(limit)
            .all()
        )

    def list_with_filters(
        self,
        skip: int = 0,
        limit: int = 100,
        status: Optional[EventStatus] = None,
    ) -> List[Event]:
        query = self.db.query(Event)
        if status:
            query = query.filter(Event.status == status)
        return query.order_by(Event.start_date.desc()).offset(skip).limit(limit).all()

    def list_upcoming(self) -> List[Event]:
        return self.db.query(Event).filter(Event.status == EventStatus.PLANNED).all()

    def list_active(self) -> List[Event]:
        return self.db.query(Event).filter(Event.status == EventStatus.IN_PROGRESS).all()
