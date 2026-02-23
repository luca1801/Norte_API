from typing import Any, Dict, List, Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from core.logger import get_logger
from enums import AuditAction
from models.audit_log import AuditLog
from models.equipment import Equipment
from models.event import Event
from models.transaction import Transaction
from models.user import User
from repositories.audit_log_repo import AuditLogRepository
from repositories.equipment_repo import EquipmentRepository
from repositories.event_repo import EventRepository
from repositories.transaction_repo import TransactionRepository
from repositories.user_repo import UserRepository

logger = get_logger(__name__)


class ReportService:
    def __init__(self, db: Session):
        self.db = db
        self.equipment_repo = EquipmentRepository(db)
        self.event_repo = EventRepository(db)
        self.transaction_repo = TransactionRepository(db)
        self.user_repo = UserRepository(db)
        self.audit_log_repo = AuditLogRepository(db)

    def get_dashboard_stats(self) -> Dict[str, Any]:
        logger.info("Fetching dashboard stats")

        total_equipment = self.db.query(func.count(Equipment.id)).scalar()
        available_equipment = self.db.query(func.count(Equipment.id)).filter(Equipment.status == "available").scalar()
        in_use_equipment = self.db.query(func.count(Equipment.id)).filter(Equipment.status == "in_use").scalar()
        maintenance_equipment = self.db.query(func.count(Equipment.id)).filter(Equipment.status == "maintenance").scalar()

        upcoming_events = self.db.query(func.count(Event.id)).filter(Event.status == "upcoming").scalar()
        active_events = self.db.query(func.count(Event.id)).filter(Event.status == "active").scalar()
        completed_events = self.db.query(func.count(Event.id)).filter(Event.status == "completed").scalar()

        pending_transactions = self.db.query(func.count(Transaction.id)).filter(Transaction.status == "pending").scalar()
        completed_transactions = self.db.query(func.count(Transaction.id)).filter(Transaction.status == "completed").scalar()

        total_users = self.db.query(func.count(User.id)).scalar()
        active_users = self.db.query(func.count(User.id)).filter(User.is_active == True).scalar()

        return {
            "equipment": {
                "total": total_equipment,
                "available": available_equipment,
                "in_use": in_use_equipment,
                "maintenance": maintenance_equipment,
            },
            "events": {
                "upcoming": upcoming_events,
                "active": active_events,
                "completed": completed_events,
            },
            "transactions": {
                "pending": pending_transactions,
                "completed": completed_transactions,
            },
            "users": {
                "total": total_users,
                "active": active_users,
            },
        }

    def get_equipment_usage_report(self) -> Dict[str, Any]:
        logger.info("Fetching equipment usage report")

        equipment_by_category = (
            self.db.query(Equipment.category, func.count(Equipment.id).label("count"))
            .group_by(Equipment.category)
            .all()
        )

        equipment_by_status = (
            self.db.query(Equipment.status, func.count(Equipment.id).label("count"))
            .group_by(Equipment.status)
            .all()
        )

        return {
            "by_category": [{"category": cat, "count": cnt} for cat, cnt in equipment_by_category],
            "by_status": [{"status": st, "count": cnt} for st, cnt in equipment_by_status],
        }

    def get_audit_log(
        self,
        skip: int = 0,
        limit: int = 100,
        table_name: Optional[str] = None,
        action: Optional[AuditAction] = None,
        user_id: Optional[str] = None,
    ) -> List[AuditLog]:
        logger.info(f"Fetching audit log with filters: table={table_name}, action={action}")
        return self.audit_log_repo.list_with_filters(skip, limit, table_name, action, user_id)

    def get_audit_log_summary(self) -> Dict[str, Any]:
        logger.info("Fetching audit log summary")

        return {
            "total": self.audit_log_repo.total_count(),
            "by_action": self.audit_log_repo.count_by_action(),
            "by_table": self.audit_log_repo.count_by_table(),
        }
