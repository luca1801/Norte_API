from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from core.database import get_db
from core.logger import get_logger
from enums import ReservationStatus
from models.user import User
from schemas.reservation import ReservationCreate, ReservationResponse, ReservationUpdate
from services.reservation_service import ReservationService
from utils.auth import get_current_manager_or_admin, get_current_user

router = APIRouter(prefix="/reservations", tags=["Reservations"])
logger = get_logger(__name__)


@router.get("/", response_model=List[ReservationResponse])
def list_reservations(
    skip: int = 0,
    limit: int = 100,
    reservation_status: Optional[ReservationStatus] = Query(None, alias="status"),
    event_id: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    logger.info(f"User {current_user.username} listing reservations")
    service = ReservationService(db)
    return service.list(skip, limit, reservation_status, event_id)


@router.get("/{reservation_id}", response_model=ReservationResponse)
def get_reservation(
    reservation_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    logger.info(f"User {current_user.username} fetching reservation ID: {reservation_id}")
    service = ReservationService(db)
    try:
        return service.get_by_id(reservation_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


@router.post("/", response_model=ReservationResponse, status_code=status.HTTP_201_CREATED)
def create_reservation(
    reservation_data: ReservationCreate,
    current_user: User = Depends(get_current_manager_or_admin),
    db: Session = Depends(get_db),
):
    logger.info(f"User {current_user.username} creating reservation")
    service = ReservationService(db)
    try:
        return service.create(reservation_data, current_user)
    except ValueError as e:
        error_msg = str(e)
        if "Conflicting reservation" in error_msg:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=error_msg,
            )
        if "not found" in error_msg.lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=error_msg,
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_msg,
        )


@router.put("/{reservation_id}", response_model=ReservationResponse)
def update_reservation(
    reservation_id: str,
    reservation_data: ReservationUpdate,
    current_user: User = Depends(get_current_manager_or_admin),
    db: Session = Depends(get_db),
):
    logger.info(f"User {current_user.username} updating reservation ID: {reservation_id}")
    service = ReservationService(db)
    try:
        return service.update(reservation_id, reservation_data)
    except ValueError as e:
        if "Conflicting reservation" in str(e):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=str(e),
            )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


@router.delete("/{reservation_id}", status_code=status.HTTP_204_NO_CONTENT)
def cancel_reservation(
    reservation_id: str,
    current_user: User = Depends(get_current_manager_or_admin),
    db: Session = Depends(get_db),
):
    logger.info(f"User {current_user.username} cancelling reservation ID: {reservation_id}")
    service = ReservationService(db)
    try:
        service.cancel(reservation_id)
    except ValueError as e:
        error_msg = str(e)
        if "not found" in error_msg.lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=error_msg,
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_msg,
        )
