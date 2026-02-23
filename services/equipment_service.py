from typing import List, Optional

from sqlalchemy.orm import Session

from core.logger import get_logger
from enums import EquipmentStatus
from models.equipment import Equipment
from repositories.equipment_repo import EquipmentRepository
from schemas.equipment import EquipmentCreate, EquipmentUpdate

logger = get_logger(__name__)


class EquipmentService:
    def __init__(self, db: Session):
        self.db = db
        self.equipment_repo = EquipmentRepository(db)

    def list(self, skip: int = 0, limit: int = 100, category: Optional[str] = None, status: Optional[EquipmentStatus] = None) -> List[Equipment]:
        logger.info(f"Listing equipment with filters: category={category}, status={status}")
        return self.equipment_repo.list_with_filters(skip, limit, category, status)

    def get_by_id(self, equipment_id: str) -> Equipment:
        logger.info(f"Fetching equipment ID: {equipment_id}")
        equipment = self.equipment_repo.get_by_id(equipment_id)
        if not equipment:
            logger.warning(f"Equipment not found: {equipment_id}")
            raise ValueError("Equipment not found")
        return equipment

    def get_by_qr_code(self, qr_code: str) -> Equipment:
        logger.info(f"Scanning QR: {qr_code}")
        equipment = self.equipment_repo.get_by_qr_code(qr_code)
        if not equipment:
            logger.warning(f"Equipment not found with QR: {qr_code}")
            raise ValueError("Equipment not found")
        return equipment

    def get_by_code(self, code: str) -> Equipment:
        logger.info(f"Fetching equipment by code: {code}")
        equipment = self.equipment_repo.get_by_code(code)
        if not equipment:
            logger.warning(f"Equipment not found with code: {code}")
            raise ValueError("Equipment not found")
        return equipment

    def create(self, equipment_data: EquipmentCreate) -> Equipment:
        logger.info(f"Creating equipment: {equipment_data.name}")

        if self.equipment_repo.exists_by_code(equipment_data.code):
            logger.warning("Equipment creation failed: Duplicate code")
            raise ValueError("Equipment code already exists")

        if equipment_data.serial and self.equipment_repo.exists_by_serial(equipment_data.serial):
            logger.warning("Equipment creation failed: Duplicate serial")
            raise ValueError("Serial number already exists")

        if equipment_data.qr_code and self.equipment_repo.exists_by_qr_code(equipment_data.qr_code):
            logger.warning("Equipment creation failed: Duplicate QR code")
            raise ValueError("QR code already exists")

        new_equipment = self.equipment_repo.create(equipment_data.model_dump())
        self.equipment_repo.commit()
        self.equipment_repo.refresh(new_equipment)

        logger.info(f"Equipment created successfully: {new_equipment.name}")
        return new_equipment

    def update(self, equipment_id: str, equipment_data: EquipmentUpdate) -> Equipment:
        logger.info(f"Updating equipment ID: {equipment_id}")

        equipment = self.equipment_repo.get_by_id(equipment_id)
        if not equipment:
            logger.warning(f"Equipment not found: {equipment_id}")
            raise ValueError("Equipment not found")

        update_data = equipment_data.model_dump(exclude_unset=True)

        new_status = update_data.get("status")
        if new_status in [EquipmentStatus.MAINTENANCE, EquipmentStatus.EXCLUDED]:
            if equipment.bag_id:
                logger.info(f"Clearing bag_id for equipment {equipment.code} due to status change to {new_status}")
                update_data["bag_id"] = None

        if "bag_id" in update_data:
            if update_data["bag_id"] == "":
                update_data["bag_id"] = None

        self.equipment_repo.update(equipment, update_data)
        self.equipment_repo.commit()
        self.equipment_repo.refresh(equipment)

        logger.info(f"Equipment updated successfully: {equipment.name}")
        return equipment

    def delete(self, equipment_id: str) -> None:
        logger.info(f"Excluding equipment ID: {equipment_id}")

        equipment = self.equipment_repo.get_by_id(equipment_id)
        if not equipment:
            logger.warning(f"Equipment not found: {equipment_id}")
            raise ValueError("Equipment not found")

        equipment.status = EquipmentStatus.EXCLUDED
        equipment.bag_id = None
        self.equipment_repo.commit()

        logger.info(f"Equipment excluded successfully: {equipment.name}")
