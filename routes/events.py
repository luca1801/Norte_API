from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from core.database import get_db
from core.logger import get_logger
from enums import EventStatus
from models.user import User
from schemas.event import EventCreate, EventResponse, EventUpdate
from services.event_service import EventService
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
    logger.info(f"User {current_user.username} listing events")
    service = EventService(db)
    return service.list(skip, limit, event_status)


@router.get("/{event_id}", response_model=EventResponse)
def get_event(
    event_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = EventService(db)
    try:
        return service.get_by_id(event_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


@router.get("/code/{code}", response_model=EventResponse)
def get_event_by_code(
    code: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = EventService(db)
    try:
        return service.get_by_code(code)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


@router.post("/", response_model=EventResponse, status_code=status.HTTP_201_CREATED)
def create_event(
    event_data: EventCreate,
    current_user: User = Depends(get_current_manager_or_admin),
    db: Session = Depends(get_db),
):
    logger.info(f"User {current_user.username} creating event: {event_data.name}")
    service = EventService(db)
    try:
        return service.create(event_data, current_user)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.put("/{event_id}", response_model=EventResponse)
def update_event(
    event_id: str,
    event_data: EventUpdate,
    current_user: User = Depends(get_current_manager_or_admin),
    db: Session = Depends(get_db),
):
    logger.info(f"User {current_user.username} updating event ID: {event_id}")
    service = EventService(db)
    try:
        return service.update(event_id, event_data)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


@router.delete("/{event_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_event(
    event_id: str,
    current_user: User = Depends(get_current_manager_or_admin),
    db: Session = Depends(get_db),
):
    logger.info(f"User {current_user.username} cancelling event ID: {event_id}")
    service = EventService(db)
    try:
        service.cancel(event_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
