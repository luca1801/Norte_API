from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from core.database import get_db
from core.logger import get_logger
from enums import EventStatus
from models.event import Event
from models.user import User
from schemas.event import EventCreate, EventResponse, EventUpdate
from utils.auth import get_current_manager_or_admin, get_current_user

router = APIRouter(prefix="/events", tags=["Events"])
logger = get_logger(__name__)


@router.get("/", response_model=List[EventResponse])
def list_events(
    skip: int = 0,
    limit: int = 100,
    event_status: Optional[EventStatus] = Query(None, alias="status"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List all events with optional filters."""
    logger.info(f"User {current_user.username} listing events")

    query = db.query(Event)

    if event_status:
        query = query.filter(Event.status == event_status)

    events = query.order_by(Event.start_date.desc()).offset(skip).limit(limit).all()
    return events


@router.get("/{event_id}", response_model=EventResponse)
def get_event(
    event_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get event by ID."""
    logger.info(f"User {current_user.username} fetching event ID: {event_id}")
    event = db.query(Event).filter(Event.id == event_id).first()

    if not event:
        logger.warning(f"Event not found: {event_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found",
        )

    return event


@router.get("/code/{code}", response_model=EventResponse)
def get_event_by_code(
    code: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get event by code."""
    logger.info(f"User {current_user.username} fetching event by code: {code}")
    event = db.query(Event).filter(Event.code == code).first()

    if not event:
        logger.warning(f"Event not found with code: {code}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found",
        )

    return event


@router.post("/", response_model=EventResponse, status_code=status.HTTP_201_CREATED)
def create_event(
    event_data: EventCreate,
    current_user: User = Depends(get_current_manager_or_admin),
    db: Session = Depends(get_db),
):
    """Create new event (manager or admin only)."""
    logger.info(f"User {current_user.username} creating event: {event_data.name}")

    # Check if code already exists
    existing = db.query(Event).filter(Event.code == event_data.code).first()
    if existing:
        logger.warning("Event creation failed: Duplicate code")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Event code already exists",
        )

    # Set owner_id to current user if not provided
    event_dict = event_data.model_dump()
    if not event_dict.get("owner_id"):
        event_dict["owner_id"] = current_user.id

    new_event = Event(**event_dict)
    db.add(new_event)
    db.commit()
    db.refresh(new_event)

    logger.info(f"Event created successfully: {new_event.name}")
    return new_event


@router.put("/{event_id}", response_model=EventResponse)
def update_event(
    event_id: str,
    event_data: EventUpdate,
    current_user: User = Depends(get_current_manager_or_admin),
    db: Session = Depends(get_db),
):
    """Update event (manager or admin only)."""
    logger.info(f"User {current_user.username} updating event ID: {event_id}")
    event = db.query(Event).filter(Event.id == event_id).first()

    if not event:
        logger.warning(f"Event not found: {event_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found",
        )

    # Update fields
    for field, value in event_data.model_dump(exclude_unset=True).items():
        setattr(event, field, value)

    db.commit()
    db.refresh(event)

    logger.info(f"Event updated successfully: {event.name}")
    return event


@router.delete("/{event_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_event(
    event_id: str,
    current_user: User = Depends(get_current_manager_or_admin),
    db: Session = Depends(get_db),
):
    """Cancel event (manager or admin only) - Sets status to CANCELLED."""
    logger.info(f"User {current_user.username} cancelling event ID: {event_id}")
    event = db.query(Event).filter(Event.id == event_id).first()

    if not event:
        logger.warning(f"Event not found: {event_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found",
        )

    # Soft delete - set status to cancelled
    event.status = EventStatus.CANCELLED
    db.commit()

    logger.info(f"Event cancelled successfully: {event.name}")
