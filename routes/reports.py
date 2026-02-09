from typing import List, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from core.database import get_db
from core.logger import get_logger
from enums import AuditAction
from models.audit_log import AuditLog
from models.equipment import Equipment
from models.event import Event
from models.transaction import Transaction
from models.user import User
from schemas.audit_log import AuditLogResponse
from utils.auth import get_current_user, get_current_admin

router = APIRouter(prefix="/reports", tags=["Reports"])
logger = get_logger(__name__)


@router.get("/dashboard")
def get_dashboard_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get dashboard statistics."""
    logger.info(f"User {current_user.username} fetching dashboard stats")

    # Equipment stats
    total_equipment = db.query(func.count(Equipment.id)).scalar()
    available_equipment = (
        db.query(func.count(Equipment.id)).filter(Equipment.status == "available").scalar()
    )
    in_use_equipment = (
        db.query(func.count(Equipment.id)).filter(Equipment.status == "in_use").scalar()
    )
    maintenance_equipment = (
        db.query(func.count(Equipment.id)).filter(Equipment.status == "maintenance").scalar()
    )

    # Event stats
    upcoming_events = db.query(func.count(Event.id)).filter(Event.status == "upcoming").scalar()
    active_events = db.query(func.count(Event.id)).filter(Event.status == "active").scalar()
    completed_events = db.query(func.count(Event.id)).filter(Event.status == "completed").scalar()

    # Transaction stats
    pending_transactions = (
        db.query(func.count(Transaction.id)).filter(Transaction.status == "pending").scalar()
    )
    completed_transactions = (
        db.query(func.count(Transaction.id)).filter(Transaction.status == "completed").scalar()
    )

    # User stats
    total_users = db.query(func.count(User.id)).scalar()
    active_users = (
        db.query(func.count(User.id)).filter(User.is_active == True).scalar()  # noqa: E712
    )

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


@router.get("/equipment-usage")
def get_equipment_usage_report(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get equipment usage report."""
    logger.info(f"User {current_user.username} fetching equipment usage report")

    # Equipment by category
    equipment_by_category = (
        db.query(Equipment.category, func.count(Equipment.id).label("count"))
        .group_by(Equipment.category)
        .all()
    )

    # Equipment by status
    equipment_by_status = (
        db.query(Equipment.status, func.count(Equipment.id).label("count"))
        .group_by(Equipment.status)
        .all()
    )

    return {
        "by_category": [{"category": cat, "count": cnt} for cat, cnt in equipment_by_category],
        "by_status": [{"status": st, "count": cnt} for st, cnt in equipment_by_status],
    }


@router.get("/audit-log", response_model=List[AuditLogResponse])
def get_audit_log(
    skip: int = 0,
    limit: int = 100,
    table_name: Optional[str] = Query(None, description="Filter by table name"),
    action: Optional[AuditAction] = Query(None, description="Filter by action type"),
    user_id: Optional[str] = Query(None, description="Filter by user ID"),
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """Get audit log entries - admin only."""
    logger.info(f"Admin {current_user.username} fetching audit log")

    query = db.query(AuditLog)

    if table_name:
        query = query.filter(AuditLog.table_name == table_name)
    if action:
        query = query.filter(AuditLog.action == action)
    if user_id:
        query = query.filter(AuditLog.user_id == user_id)

    audit_entries = query.order_by(AuditLog.created_at.desc()).offset(skip).limit(limit).all()
    return audit_entries


@router.get("/audit-log/summary")
def get_audit_log_summary(
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """Get audit log summary statistics - admin only."""
    logger.info(f"Admin {current_user.username} fetching audit log summary")

    # Count by action
    by_action = (
        db.query(AuditLog.action, func.count(AuditLog.id).label("count"))
        .group_by(AuditLog.action)
        .all()
    )

    # Count by table
    by_table = (
        db.query(AuditLog.table_name, func.count(AuditLog.id).label("count"))
        .group_by(AuditLog.table_name)
        .all()
    )

    # Total count
    total = db.query(func.count(AuditLog.id)).scalar()

    return {
        "total": total,
        "by_action": [
            {"action": a.value if hasattr(a, "value") else a, "count": c} for a, c in by_action
        ],
        "by_table": [{"table": t, "count": c} for t, c in by_table],
    }
