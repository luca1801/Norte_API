"""
Routes for Bag management.
"""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from core.database import get_db
from core.logger import get_logger
from enums import BagStatus
from models.bag import Bag
from models.equipment import Equipment
from models.user import User
from schemas.bag import BagCreate, BagResponse, BagUpdate, BagWithEquipment
from utils.auth import get_current_admin, get_current_user

router = APIRouter(prefix="/bags", tags=["Bags"])
logger = get_logger(__name__)


@router.get("/", response_model=List[BagResponse])
def list_bags(
    skip: int = 0,
    limit: int = 100,
    status_filter: Optional[BagStatus] = Query(None, alias="status"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List all bags with optional filters."""
    logger.info(f"User {current_user.username} listing bags")

    query = db.query(Bag)

    if status_filter is not None:
        query = query.filter(Bag.status == status_filter)
    else:
        # Por padrão, não mostrar bags excluídas
        query = query.filter(Bag.status != BagStatus.EXCLUDED)

    bags = query.offset(skip).limit(limit).all()

    # Add equipment count to each bag
    result = []
    for bag in bags:
        bag_dict = BagResponse.model_validate(bag).model_dump()
        bag_dict["equipment_count"] = len(bag.equipment_items) if bag.equipment_items else 0
        result.append(BagResponse(**bag_dict))

    return result


@router.get("/{bag_id}", response_model=BagWithEquipment)
def get_bag(
    bag_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get bag by ID with equipment items."""
    logger.info(f"User {current_user.username} fetching bag ID: {bag_id}")
    bag = db.query(Bag).filter(Bag.id == bag_id).first()

    if not bag:
        logger.warning(f"Bag not found: {bag_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bag not found",
        )

    return bag


@router.get("/code/{code}", response_model=BagWithEquipment)
def get_bag_by_code(
    code: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get bag by code."""
    logger.info(f"User {current_user.username} fetching bag by code: {code}")
    bag = db.query(Bag).filter(Bag.code == code).first()

    if not bag:
        logger.warning(f"Bag not found with code: {code}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bag not found",
        )

    return bag


@router.post("/", response_model=BagResponse, status_code=status.HTTP_201_CREATED)
def create_bag(
    bag_data: BagCreate,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """Create new bag (admin only)."""
    logger.info(f"User {current_user.username} creating bag: {bag_data.name}")

    # Check if code already exists
    existing = db.query(Bag).filter(Bag.code == bag_data.code).first()
    if existing:
        logger.warning("Bag creation failed: Duplicate code")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Bag code already exists",
        )

    new_bag = Bag(**bag_data.model_dump())
    db.add(new_bag)
    db.commit()
    db.refresh(new_bag)

    logger.info(f"Bag created successfully: {new_bag.name}")
    return new_bag


@router.put("/{bag_id}", response_model=BagResponse)
def update_bag(
    bag_id: str,
    bag_data: BagUpdate,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """Update bag (admin only)."""
    logger.info(f"User {current_user.username} updating bag ID: {bag_id}")
    bag = db.query(Bag).filter(Bag.id == bag_id).first()

    if not bag:
        logger.warning(f"Bag not found: {bag_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bag not found",
        )

    # Update fields
    for field, value in bag_data.model_dump(exclude_unset=True).items():
        setattr(bag, field, value)

    db.commit()
    db.refresh(bag)

    logger.info(f"Bag updated successfully: {bag.name}")
    return bag


@router.delete("/{bag_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_bag(
    bag_id: str,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """Delete bag (admin only) - Soft delete by setting status to EXCLUDED."""
    logger.info(f"User {current_user.username} excluding bag ID: {bag_id}")
    bag = db.query(Bag).filter(Bag.id == bag_id).first()

    if not bag:
        logger.warning(f"Bag not found: {bag_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bag not found",
        )

    # Soft delete - set status to EXCLUDED
    bag.status = BagStatus.EXCLUDED
    db.commit()

    logger.info(f"Bag excluded successfully: {bag.name}")


@router.post("/{bag_id}/equipment/{equipment_code}", response_model=BagResponse)
def add_equipment_to_bag(
    bag_id: str,
    equipment_code: str,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """Add equipment to bag by equipment code (admin only)."""
    logger.info(f"User {current_user.username} adding equipment {equipment_code} to bag {bag_id}")

    # Buscar bag
    bag = db.query(Bag).filter(Bag.id == bag_id).first()
    if not bag:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bag not found",
        )

    if bag.status == BagStatus.EXCLUDED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot add equipment to excluded bag",
        )

    # Buscar equipamento pelo código (case-insensitive)
    equipment = db.query(Equipment).filter(Equipment.code.ilike(equipment_code)).first()

    if not equipment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Equipment with code '{equipment_code}' not found",
        )

    # Verificar se equipamento já está em outra bag
    if equipment.bag_id and equipment.bag_id != bag_id:
        other_bag = db.query(Bag).filter(Bag.id == equipment.bag_id).first()
        other_bag_name = other_bag.name if other_bag else "outra bag"
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Equipment already belongs to '{other_bag_name}' ({other_bag.code if other_bag else 'unknown'})",
        )

    # Verificar se equipamento já está nesta bag
    if equipment.bag_id == bag_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Equipment already in this bag",
        )

    # Adicionar equipamento à bag
    equipment.bag_id = bag_id
    db.commit()
    db.refresh(bag)

    # Retornar bag com equipment_count atualizado
    bag_response = BagResponse.model_validate(bag).model_dump()
    bag_response["equipment_count"] = len(bag.equipment_items)

    logger.info(f"Equipment {equipment.code} added to bag {bag.code}")
    return BagResponse(**bag_response)


@router.delete("/{bag_id}/equipment/{equipment_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_equipment_from_bag(
    bag_id: str,
    equipment_id: str,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """Remove equipment from bag (admin only)."""
    logger.info(f"User {current_user.username} removing equipment {equipment_id} from bag {bag_id}")

    # Buscar bag
    bag = db.query(Bag).filter(Bag.id == bag_id).first()
    if not bag:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bag not found",
        )

    # Buscar equipamento
    equipment = db.query(Equipment).filter(Equipment.id == equipment_id).first()
    if not equipment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Equipment not found",
        )

    # Verificar se equipamento pertence a esta bag
    if equipment.bag_id != bag_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Equipment does not belong to this bag",
        )

    # Remover equipamento da bag
    equipment.bag_id = None
    db.commit()

    logger.info(f"Equipment {equipment.code} removed from bag {bag.code}")
