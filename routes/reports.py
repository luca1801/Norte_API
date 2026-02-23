from typing import List, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from core.database import get_db
from core.logger import get_logger
from enums import AuditAction
from models.user import User
from schemas.audit_log import AuditLogResponse
from services.report_service import ReportService
from utils.auth import get_current_user, get_current_admin

router = APIRouter(prefix="/reports", tags=["Reports"])
logger = get_logger(__name__)


@router.get("/dashboard")
def get_dashboard_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    logger.info(f"User {current_user.username} fetching dashboard stats")
    service = ReportService(db)
    return service.get_dashboard_stats()


@router.get("/equipment-usage")
def get_equipment_usage_report(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    logger.info(f"User {current_user.username} fetching equipment usage report")
    service = ReportService(db)
    return service.get_equipment_usage_report()


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
    logger.info(f"Admin {current_user.username} fetching audit log")
    service = ReportService(db)
    return service.get_audit_log(skip, limit, table_name, action, user_id)


@router.get("/audit-log/summary")
def get_audit_log_summary(
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    logger.info(f"Admin {current_user.username} fetching audit log summary")
    service = ReportService(db)
    return service.get_audit_log_summary()
