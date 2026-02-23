from typing import Any, Dict, Generic, List, Optional, Type, TypeVar, Union
from uuid import UUID

from sqlalchemy.orm import Query, Session

from core.logger import get_logger

ModelType = TypeVar("ModelType")
logger = get_logger(__name__)


class BaseRepository(Generic[ModelType]):
    def __init__(self, model: Type[ModelType], db: Session):
        self.model = model
        self.db = db

    def get_by_id(self, id: Union[str, UUID]) -> Optional[ModelType]:
        return self.db.query(self.model).filter(self.model.id == id).first()

    def get_by_field(self, field: str, value: Any) -> Optional[ModelType]:
        return self.db.query(self.model).filter(getattr(self.model, field) == value).first()

    def get_by_field_ilike(self, field: str, value: str) -> Optional[ModelType]:
        return self.db.query(self.model).filter(getattr(self.model, field).ilike(value)).first()

    def list(
        self,
        skip: int = 0,
        limit: int = 100,
        filters: Optional[Dict[str, Any]] = None,
        order_by: Optional[Any] = None,
        order_desc: bool = False,
    ) -> List[ModelType]:
        query: Query = self.db.query(self.model)

        if filters:
            for field, value in filters.items():
                if hasattr(self.model, field) and value is not None:
                    query = query.filter(getattr(self.model, field) == value)

        if order_by is not None:
            if order_desc:
                query = query.order_by(order_by.desc())
            else:
                query = query.order_by(order_by)

        return query.offset(skip).limit(limit).all()

    def list_all(self) -> List[ModelType]:
        return self.db.query(self.model).all()

    def create(self, data: Dict[str, Any]) -> ModelType:
        instance = self.model(**data)
        self.db.add(instance)
        self.db.flush()
        return instance

    def update(self, instance: ModelType, data: Dict[str, Any]) -> ModelType:
        for field, value in data.items():
            if hasattr(instance, field):
                setattr(instance, field, value)
        self.db.flush()
        return instance

    def delete(self, instance: ModelType) -> None:
        self.db.delete(instance)
        self.db.flush()

    def soft_delete(self, instance: ModelType, status_field: str = "status", status_value: Any = None) -> ModelType:
        if hasattr(instance, status_field) and status_value is not None:
            setattr(instance, status_field, status_value)
        self.db.flush()
        return instance

    def exists_by_id(self, id: Union[str, UUID]) -> bool:
        return self.db.query(self.model).filter(self.model.id == id).first() is not None

    def exists_by_field(self, field: str, value: Any) -> bool:
        return self.db.query(self.model).filter(getattr(self.model, field) == value).first() is not None

    def count(self, filters: Optional[Dict[str, Any]] = None) -> int:
        query = self.db.query(self.model)
        if filters:
            for field, value in filters.items():
                if hasattr(self.model, field) and value is not None:
                    query = query.filter(getattr(self.model, field) == value)
        return query.count()

    def commit(self) -> None:
        self.db.commit()

    def refresh(self, instance: ModelType) -> ModelType:
        self.db.refresh(instance)
        return instance
