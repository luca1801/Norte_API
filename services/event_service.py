from typing import List, Optional
from uuid import UUID

from sqlalchemy.orm import Session

from core.logger import get_logger
from enums import EventStatus
from models.event import Event
from models.user import User
from repositories.event_repo import EventRepository
from schemas.event import EventCreate, EventUpdate

logger = get_logger(__name__)


class EventService:
    def __init__(self, db: Session):
        self.db = db
        self.event_repo = EventRepository(db)

    def list(self, skip: int = 0, limit: int = 100, status: Optional[EventStatus] = None) -> List[Event]:
        logger.info(f"Listing events with filter: status={status}")
        return self.event_repo.list_with_filters(skip, limit, status)

    def get_by_id(self, event_id: str) -> Event:
        logger.info(f"Fetching event ID: {event_id}")
        event = self.event_repo.get_by_id(event_id)
        if not event:
            logger.warning(f"Event not found: {event_id}")
            raise ValueError("Event not found")
        return event

    def get_by_code(self, code: str) -> Event:
        logger.info(f"Fetching event by code: {code}")
        event = self.event_repo.get_by_code(code)
        if not event:
            logger.warning(f"Event not found with code: {code}")
            raise ValueError("Event not found")
        return event

    def create(self, event_data: EventCreate, current_user: User) -> Event:
        logger.info(f"Creating event: {event_data.name}")

        if self.event_repo.exists_by_code(event_data.code):
            logger.warning("Event creation failed: Duplicate code")
            raise ValueError("Event code already exists")

        event_dict = event_data.model_dump()
        if not event_dict.get("owner_id"):
            event_dict["owner_id"] = current_user.id

        new_event = self.event_repo.create(event_dict)
        self.event_repo.commit()
        self.event_repo.refresh(new_event)

        logger.info(f"Event created successfully: {new_event.name}")
        return new_event

    def update(self, event_id: str, event_data: EventUpdate) -> Event:
        logger.info(f"Updating event ID: {event_id}")

        event = self.event_repo.get_by_id(event_id)
        if not event:
            logger.warning(f"Event not found: {event_id}")
            raise ValueError("Event not found")

        self.event_repo.update(event, event_data.model_dump(exclude_unset=True))
        self.event_repo.commit()
        self.event_repo.refresh(event)

        logger.info(f"Event updated successfully: {event.name}")
        return event

    def cancel(self, event_id: str) -> None:
        logger.info(f"Cancelling event ID: {event_id}")

        event = self.event_repo.get_by_id(event_id)
        if not event:
            logger.warning(f"Event not found: {event_id}")
            raise ValueError("Event not found")

        event.status = EventStatus.CANCELLED
        self.event_repo.commit()

        logger.info(f"Event cancelled successfully: {event.name}")
