from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from core.database import get_db
from core.logger import get_logger
from enums import EquipmentStatus
from models.equipment import Equipment
from models.user import User
from schemas.equipment import EquipmentCreate, EquipmentResponse, EquipmentUpdate
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
    """List all equipment with optional filters."""
    logger.info(f"User {current_user.username} listing equipment")

    query = db.query(Equipment)

    if category:
        query = query.filter(Equipment.category == category)
    if equipment_status:
        query = query.filter(Equipment.status == equipment_status)

    equipment_list = query.offset(skip).limit(limit).all()
    return equipment_list


@router.get("/{equipment_id}", response_model=EquipmentResponse)
def get_equipment(
    equipment_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get equipment by ID."""
    logger.info(f"User {current_user.username} fetching equipment ID: {equipment_id}")
    equipment = db.query(Equipment).filter(Equipment.id == equipment_id).first()

    if not equipment:
        logger.warning(f"Equipment not found: {equipment_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Equipment not found",
        )

    return equipment


@router.get("/qr/{qr_code}", response_model=EquipmentResponse)
def get_equipment_by_qr(
    qr_code: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get equipment by QR code."""
    logger.info(f"User {current_user.username} scanning QR: {qr_code}")
    equipment = db.query(Equipment).filter(Equipment.qr_code == qr_code).first()

    if not equipment:
        logger.warning(f"Equipment not found with QR: {qr_code}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Equipment not found",
        )

    return equipment


@router.get("/code/{code}", response_model=EquipmentResponse)
def get_equipment_by_code(
    code: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get equipment by code."""
    logger.info(f"User {current_user.username} fetching equipment by code: {code}")
    equipment = db.query(Equipment).filter(Equipment.code == code).first()

    if not equipment:
        logger.warning(f"Equipment not found with code: {code}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Equipment not found",
        )

    return equipment


@router.post("/", response_model=EquipmentResponse, status_code=status.HTTP_201_CREATED)
def create_equipment(
    equipment_data: EquipmentCreate,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """Create new equipment (admin only)."""
    logger.info(f"User {current_user.username} creating equipment: {equipment_data.name}")

    # Check if code already exists
    existing = db.query(Equipment).filter(Equipment.code == equipment_data.code).first()
    if existing:
        logger.warning("Equipment creation failed: Duplicate code")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Equipment code already exists",
        )

    # Check if serial already exists (if provided)
    if equipment_data.serial:
        existing_serial = (
            db.query(Equipment).filter(Equipment.serial == equipment_data.serial).first()
        )
        if existing_serial:
            logger.warning("Equipment creation failed: Duplicate serial")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Serial number already exists",
            )

    # Check if QR code already exists (if provided)
    if equipment_data.qr_code:
        existing_qr = (
            db.query(Equipment).filter(Equipment.qr_code == equipment_data.qr_code).first()
        )
        if existing_qr:
            logger.warning("Equipment creation failed: Duplicate QR code")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="QR code already exists",
            )

    new_equipment = Equipment(**equipment_data.model_dump())
    db.add(new_equipment)
    db.commit()
    db.refresh(new_equipment)

    logger.info(f"Equipment created successfully: {new_equipment.name}")
    return new_equipment


@router.put("/{equipment_id}", response_model=EquipmentResponse)
def update_equipment(
    equipment_id: str,
    equipment_data: EquipmentUpdate,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """Update equipment (admin only)."""
    logger.info(f"User {current_user.username} updating equipment ID: {equipment_id}")
    equipment = db.query(Equipment).filter(Equipment.id == equipment_id).first()

    if not equipment:
        logger.warning(f"Equipment not found: {equipment_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Equipment not found",
        )

    # Update fields
    update_data = equipment_data.model_dump(exclude_unset=True)

    # RN02.3: Se status mudar para maintenance ou excluded, limpar bag_id
    new_status = update_data.get("status")
    if new_status in [EquipmentStatus.MAINTENANCE, EquipmentStatus.EXCLUDED]:
        if equipment.bag_id:
            logger.info(
                f"Clearing bag_id for equipment {equipment.code} due to status change to {new_status}"
            )
            update_data["bag_id"] = None

    # Tratar bag_id enviado explicitamente (incluindo null para limpar)
    if "bag_id" in update_data:
        # Se bag_id for string vazia, tratar como None
        if update_data["bag_id"] == "":
            update_data["bag_id"] = None

    for field, value in update_data.items():
        setattr(equipment, field, value)

    db.commit()
    db.refresh(equipment)

    logger.info(f"Equipment updated successfully: {equipment.name}")
    return equipment


@router.delete("/{equipment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_equipment(
    equipment_id: str,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """Delete equipment (admin only) - Sets status to EXCLUDED and removes from bag."""
    logger.info(f"User {current_user.username} excluding equipment ID: {equipment_id}")
    equipment = db.query(Equipment).filter(Equipment.id == equipment_id).first()

    if not equipment:
        logger.warning(f"Equipment not found: {equipment_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Equipment not found",
        )

    # Soft delete - set status to excluded and remove from bag
    equipment.status = EquipmentStatus.EXCLUDED
    equipment.bag_id = None  # Remove from bag when excluded
    db.commit()

    logger.info(f"Equipment excluded successfully: {equipment.name}")
