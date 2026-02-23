from typing import Any, Dict, List, Optional, Union
from uuid import UUID

from sqlalchemy import func
from sqlalchemy.orm import Session

from enums import AuditAction
from models.audit_log import AuditLog
from repositories.base import BaseRepository


class AuditLogRepository(BaseRepository[AuditLog]):
    def __init__(self, db: Session):
        super().__init__(AuditLog, db)

    def list_with_filters(
        self,
        skip: int = 0,
        limit: int = 100,
        table_name: Optional[str] = None,
        action: Optional[AuditAction] = None,
        user_id: Optional[Union[str, UUID]] = None,
    ) -> List[AuditLog]:
        query = self.db.query(AuditLog)
        if table_name:
            query = query.filter(AuditLog.table_name == table_name)
        if action:
            query = query.filter(AuditLog.action == action)
        if user_id:
            query = query.filter(AuditLog.user_id == user_id)
        return query.order_by(AuditLog.created_at.desc()).offset(skip).limit(limit).all()

    def count_by_action(self) -> List[Dict[str, Any]]:
        results = (
            self.db.query(AuditLog.action, func.count(AuditLog.id).label("count"))
            .group_by(AuditLog.action)
            .all()
        )
        return [{"action": r.action.value if hasattr(r.action, "value") else r.action, "count": r.count} for r in results]

    def count_by_table(self) -> List[Dict[str, Any]]:
        results = (
            self.db.query(AuditLog.table_name, func.count(AuditLog.id).label("count"))
            .group_by(AuditLog.table_name)
            .all()
        )
        return [{"table": r.table_name, "count": r.count} for r in results]

    def total_count(self) -> int:
        return self.db.query(func.count(AuditLog.id)).scalar()
