from typing import List, Optional

from sqlalchemy.orm import Session

from core.logger import get_logger
from enums import BagStatus
from models.bag import Bag
from models.equipment import Equipment
from repositories.bag_repo import BagRepository
from repositories.equipment_repo import EquipmentRepository
from schemas.bag import BagCreate, BagUpdate

logger = get_logger(__name__)


class BagService:
    def __init__(self, db: Session):
        self.db = db
        self.bag_repo = BagRepository(db)
        self.equipment_repo = EquipmentRepository(db)

    def list(self, skip: int = 0, limit: int = 100, status: Optional[BagStatus] = None) -> List[dict]:
        logger.info(f"Listing bags with filter: status={status}")
        exclude_status = None if status else BagStatus.EXCLUDED
        return self.bag_repo.list_with_equipment_count(skip, limit, status, exclude_status)

    def get_by_id(self, bag_id: str) -> Bag:
        logger.info(f"Fetching bag ID: {bag_id}")
        bag = self.bag_repo.get_by_id(bag_id)
        if not bag:
            logger.warning(f"Bag not found: {bag_id}")
            raise ValueError("Bag not found")
        return bag

    def get_by_code(self, code: str) -> Bag:
        logger.info(f"Fetching bag by code: {code}")
        bag = self.bag_repo.get_by_code(code)
        if not bag:
            logger.warning(f"Bag not found with code: {code}")
            raise ValueError("Bag not found")
        return bag

    def create(self, bag_data: BagCreate) -> Bag:
        logger.info(f"Creating bag: {bag_data.name}")

        if self.bag_repo.exists_by_code(bag_data.code):
            logger.warning("Bag creation failed: Duplicate code")
            raise ValueError("Bag code already exists")

        new_bag = self.bag_repo.create(bag_data.model_dump())
        self.bag_repo.commit()
        self.bag_repo.refresh(new_bag)

        logger.info(f"Bag created successfully: {new_bag.name}")
        return new_bag

    def update(self, bag_id: str, bag_data: BagUpdate) -> Bag:
        logger.info(f"Updating bag ID: {bag_id}")

        bag = self.bag_repo.get_by_id(bag_id)
        if not bag:
            logger.warning(f"Bag not found: {bag_id}")
            raise ValueError("Bag not found")

        self.bag_repo.update(bag, bag_data.model_dump(exclude_unset=True))
        self.bag_repo.commit()
        self.bag_repo.refresh(bag)

        logger.info(f"Bag updated successfully: {bag.name}")
        return bag

    def delete(self, bag_id: str) -> None:
        logger.info(f"Excluding bag ID: {bag_id}")

        bag = self.bag_repo.get_by_id(bag_id)
        if not bag:
            logger.warning(f"Bag not found: {bag_id}")
            raise ValueError("Bag not found")

        bag.status = BagStatus.EXCLUDED
        self.bag_repo.commit()

        logger.info(f"Bag excluded successfully: {bag.name}")

    def add_equipment(self, bag_id: str, equipment_code: str) -> dict:
        logger.info(f"Adding equipment {equipment_code} to bag {bag_id}")

        bag = self.bag_repo.get_by_id(bag_id)
        if not bag:
            raise ValueError("Bag not found")

        if bag.status == BagStatus.EXCLUDED:
            raise ValueError("Cannot add equipment to excluded bag")

        equipment = self.equipment_repo.get_by_code_ilike(equipment_code)
        if not equipment:
            raise ValueError(f"Equipment with code '{equipment_code}' not found")

        if equipment.bag_id and str(equipment.bag_id) != bag_id:
            other_bag = self.bag_repo.get_by_id(equipment.bag_id)
            other_bag_name = other_bag.name if other_bag else "outra bag"
            raise ValueError(f"Equipment already belongs to '{other_bag_name}'")

        if equipment.bag_id and str(equipment.bag_id) == bag_id:
            raise ValueError("Equipment already in this bag")

        equipment.bag_id = bag_id
        self.bag_repo.commit()
        self.bag_repo.refresh(bag)

        bag_response = {
            "id": bag.id,
            "code": bag.code,
            "name": bag.name,
            "description": bag.description,
            "status": bag.status,
            "is_active": bag.is_active,
            "created_at": bag.created_at,
            "updated_at": bag.updated_at,
            "equipment_count": len(bag.equipment_items) if bag.equipment_items else 0,
        }

        logger.info(f"Equipment {equipment.code} added to bag {bag.code}")
        return bag_response

    def remove_equipment(self, bag_id: str, equipment_id: str) -> None:
        logger.info(f"Removing equipment {equipment_id} from bag {bag_id}")

        bag = self.bag_repo.get_by_id(bag_id)
        if not bag:
            raise ValueError("Bag not found")

        equipment = self.equipment_repo.get_by_id(equipment_id)
        if not equipment:
            raise ValueError("Equipment not found")

        if str(equipment.bag_id) != bag_id:
            raise ValueError("Equipment does not belong to this bag")

        equipment.bag_id = None
        self.bag_repo.commit()

        logger.info(f"Equipment {equipment.code} removed from bag {bag.code}")
