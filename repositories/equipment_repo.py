from typing import List, Optional, Union
from uuid import UUID

from sqlalchemy.orm import Session

from enums import EquipmentStatus
from models.equipment import Equipment
from repositories.base import BaseRepository


class EquipmentRepository(BaseRepository[Equipment]):
    def __init__(self, db: Session):
        super().__init__(Equipment, db)

    def get_by_code(self, code: str) -> Optional[Equipment]:
        return self.db.query(Equipment).filter(Equipment.code == code).first()

    def get_by_code_ilike(self, code: str) -> Optional[Equipment]:
        return self.db.query(Equipment).filter(Equipment.code.ilike(code)).first()

    def get_by_qr_code(self, qr_code: str) -> Optional[Equipment]:
        return self.db.query(Equipment).filter(Equipment.qr_code == qr_code).first()

    def get_by_serial(self, serial: str) -> Optional[Equipment]:
        return self.db.query(Equipment).filter(Equipment.serial == serial).first()

    def exists_by_code(self, code: str) -> bool:
        return self.db.query(Equipment).filter(Equipment.code == code).first() is not None

    def exists_by_qr_code(self, qr_code: str) -> bool:
        return self.db.query(Equipment).filter(Equipment.qr_code == qr_code).first() is not None

    def exists_by_serial(self, serial: str) -> bool:
        return self.db.query(Equipment).filter(Equipment.serial == serial).first() is not None

    def list_by_status(
        self, status: EquipmentStatus, skip: int = 0, limit: int = 100
    ) -> List[Equipment]:
        return (
            self.db.query(Equipment)
            .filter(Equipment.status == status)
            .offset(skip)
            .limit(limit)
            .all()
        )

    def list_by_category(
        self, category: str, skip: int = 0, limit: int = 100
    ) -> List[Equipment]:
        return (
            self.db.query(Equipment)
            .filter(Equipment.category == category)
            .offset(skip)
            .limit(limit)
            .all()
        )

    def list_by_bag(self, bag_id: Union[str, UUID]) -> List[Equipment]:
        return self.db.query(Equipment).filter(Equipment.bag_id == bag_id).all()

    def list_with_filters(
        self,
        skip: int = 0,
        limit: int = 100,
        category: Optional[str] = None,
        status: Optional[EquipmentStatus] = None,
    ) -> List[Equipment]:
        query = self.db.query(Equipment)
        if category:
            query = query.filter(Equipment.category == category)
        if status:
            query = query.filter(Equipment.status == status)
        return query.offset(skip).limit(limit).all()
