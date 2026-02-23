from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from core.database import get_db
from core.logger import get_logger
from enums import BagStatus
from schemas.bag import BagCreate, BagResponse, BagUpdate, BagWithEquipment
from services.bag_service import BagService
from utils.auth import get_current_admin, get_current_user

router = APIRouter(prefix="/bags", tags=["Bags"])
logger = get_logger(__name__)


@router.get("/", response_model=List[BagResponse])
def list_bags(
    skip: int = 0,
    limit: int = 100,
    status_filter: Optional[BagStatus] = Query(None, alias="status"),
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    logger.info(f"User {current_user.username} listing bags")
    service = BagService(db)
    bags = service.list(skip, limit, status_filter)
    return [BagResponse(**bag) for bag in bags]


@router.get("/{bag_id}", response_model=BagWithEquipment)
def get_bag(
    bag_id: str,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    logger.info(f"User {current_user.username} fetching bag ID: {bag_id}")
    service = BagService(db)
    try:
        return service.get_by_id(bag_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


@router.get("/code/{code}", response_model=BagWithEquipment)
def get_bag_by_code(
    code: str,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    logger.info(f"User {current_user.username} fetching bag by code: {code}")
    service = BagService(db)
    try:
        return service.get_by_code(code)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


@router.post("/", response_model=BagResponse, status_code=status.HTTP_201_CREATED)
def create_bag(
    bag_data: BagCreate,
    current_user = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    logger.info(f"User {current_user.username} creating bag: {bag_data.name}")
    service = BagService(db)
    try:
        return service.create(bag_data)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.put("/{bag_id}", response_model=BagResponse)
def update_bag(
    bag_id: str,
    bag_data: BagUpdate,
    current_user = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    logger.info(f"User {current_user.username} updating bag ID: {bag_id}")
    service = BagService(db)
    try:
        return service.update(bag_id, bag_data)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


@router.delete("/{bag_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_bag(
    bag_id: str,
    current_user = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    logger.info(f"User {current_user.username} excluding bag ID: {bag_id}")
    service = BagService(db)
    try:
        service.delete(bag_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


@router.post("/{bag_id}/equipment/{equipment_code}", response_model=BagResponse)
def add_equipment_to_bag(
    bag_id: str,
    equipment_code: str,
    current_user = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    logger.info(f"User {current_user.username} adding equipment {equipment_code} to bag {bag_id}")
    service = BagService(db)
    try:
        result = service.add_equipment(bag_id, equipment_code)
        return BagResponse(**result)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.delete("/{bag_id}/equipment/{equipment_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_equipment_from_bag(
    bag_id: str,
    equipment_id: str,
    current_user = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    logger.info(f"User {current_user.username} removing equipment {equipment_id} from bag {bag_id}")
    service = BagService(db)
    try:
        service.remove_equipment(bag_id, equipment_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
