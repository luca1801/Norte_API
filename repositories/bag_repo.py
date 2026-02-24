from typing import List, Optional, Union
from uuid import UUID

from sqlalchemy.orm import Session

from enums import BagStatus
from models.bag import Bag
from repositories.base import BaseRepository


class BagRepository(BaseRepository[Bag]):
    def __init__(self, db: Session):
        super().__init__(Bag, db)

    def get_by_code(self, code: str) -> Optional[Bag]:
        return self.db.query(Bag).filter(Bag.code == code).first()

    def exists_by_code(self, code: str) -> bool:
        return self.db.query(Bag).filter(Bag.code == code).first() is not None

    def list_by_status(
        self, status: BagStatus, skip: int = 0, limit: int = 100
    ) -> List[Bag]:
        return (
            self.db.query(Bag)
            .filter(Bag.status == status)
            .offset(skip)
            .limit(limit)
            .all()
        )

    def list_with_filters(
        self,
        skip: int = 0,
        limit: int = 100,
        status: Optional[BagStatus] = None,
        exclude_status: Optional[BagStatus] = None,
    ) -> List[Bag]:
        query = self.db.query(Bag)
        if status:
            query = query.filter(Bag.status == status)
        if exclude_status:
            query = query.filter(Bag.status != exclude_status)
        return query.offset(skip).limit(limit).all()

    def list_with_equipment_count(
        self,
        skip: int = 0,
        limit: int = 100,
        status: Optional[BagStatus] = None,
        exclude_status: Optional[BagStatus] = None,
    ) -> List[dict]:
        bags = self.list_with_filters(skip, limit, status, exclude_status)
        result = []
        for bag in bags:
            bag_dict = {
                "id": bag.id,
                "code": bag.code,
                "name": bag.name,
                "description": bag.description,
                "status": bag.status,
                "current_event_id": bag.current_event_id,
                "is_active": bag.is_active,
                "created_at": bag.created_at,
                "updated_at": bag.updated_at,
                "equipment_count": len(bag.equipment_items) if bag.equipment_items else 0,
            }
            result.append(bag_dict)
        return result
