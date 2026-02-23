from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from core.database import get_db
from core.logger import get_logger
from enums import EquipmentStatus
from models.user import User
from schemas.equipment import EquipmentCreate, EquipmentResponse, EquipmentUpdate
from services.equipment_service import EquipmentService
from utils.auth import get_current_admin, get_current_user

router = APIRouter(prefix="/equipment", tags=["Equipment"])
logger = get_logger(__name__)


@router.get("/", response_model=List[EquipmentResponse])
def list_equipment(
    skip: int = 0,
    limit: int = 100,
    category: Optional[str] = Query(None),
    equipment_status: Optional[EquipmentStatus] = Query(None, alias="status"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    logger.info(f"User {current_user.username} listing equipment")
    service = EquipmentService(db)
    return service.list(skip, limit, category, equipment_status)


@router.get("/{equipment_id}", response_model=EquipmentResponse)
def get_equipment(
    equipment_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = EquipmentService(db)
    try:
        return service.get_by_id(equipment_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


@router.get("/qr/{qr_code}", response_model=EquipmentResponse)
def get_equipment_by_qr(
    qr_code: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = EquipmentService(db)
    try:
        return service.get_by_qr_code(qr_code)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


@router.get("/code/{code}", response_model=EquipmentResponse)
def get_equipment_by_code(
    code: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = EquipmentService(db)
    try:
        return service.get_by_code(code)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


@router.post("/", response_model=EquipmentResponse, status_code=status.HTTP_201_CREATED)
def create_equipment(
    equipment_data: EquipmentCreate,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    logger.info(f"User {current_user.username} creating equipment: {equipment_data.name}")
    service = EquipmentService(db)
    try:
        return service.create(equipment_data)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.put("/{equipment_id}", response_model=EquipmentResponse)
def update_equipment(
    equipment_id: str,
    equipment_data: EquipmentUpdate,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    logger.info(f"User {current_user.username} updating equipment ID: {equipment_id}")
    service = EquipmentService(db)
    try:
        return service.update(equipment_id, equipment_data)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


@router.delete("/{equipment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_equipment(
    equipment_id: str,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    logger.info(f"User {current_user.username} excluding equipment ID: {equipment_id}")
    service = EquipmentService(db)
    try:
        service.delete(equipment_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
