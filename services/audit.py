"""
Serviço de Auditoria para registrar todas as mudanças no sistema.
"""

import json
from typing import Any, Dict, Optional

from sqlalchemy.orm import Session

from core.logger import get_logger
from enums import AuditAction
from models.audit_log import AuditLog

logger = get_logger(__name__)


def serialize_value(value: Any) -> Any:
    """Serializa valores para JSON, tratando tipos especiais."""
    if value is None:
        return None
    if hasattr(value, "value"):  # Enum
        return value.value
    if hasattr(value, "isoformat"):  # datetime
        return value.isoformat()
    return str(value)


def model_to_dict(model: Any, exclude_fields: Optional[list] = None) -> Dict[str, Any]:
    """Converte um modelo SQLAlchemy para dicionário."""
    exclude = exclude_fields or ["_sa_instance_state"]
    result = {}
    for column in model.__table__.columns:
        if column.name not in exclude:
            value = getattr(model, column.name)
            result[column.name] = serialize_value(value)
    return result


def create_audit_log(
    db: Session,
    table_name: str,
    record_id: str,
    action: AuditAction,
    old_values: Optional[Dict[str, Any]] = None,
    new_values: Optional[Dict[str, Any]] = None,
    user_id: Optional[str] = None,
    ip_address: Optional[str] = None,
) -> AuditLog:
    """
    Cria um registro de auditoria no banco de dados.

    Args:
        db: Sessão do banco de dados
        table_name: Nome da tabela afetada
        record_id: ID do registro afetado
        action: Tipo de ação (INSERT, UPDATE, DELETE)
        old_values: Valores antigos (para UPDATE e DELETE)
        new_values: Valores novos (para INSERT e UPDATE)
        user_id: ID do usuário que realizou a ação
        ip_address: Endereço IP de origem

    Returns:
        AuditLog: Registro de auditoria criado
    """
    try:
        audit = AuditLog(
            table_name=table_name,
            record_id=record_id,
            action=action,
            old_values=json.dumps(old_values) if old_values else None,
            new_values=json.dumps(new_values) if new_values else None,
            user_id=user_id,
            ip_address=ip_address,
        )
        db.add(audit)
        # Não commit aqui - deixar para a função que chamou fazer commit
        logger.info("Audit log created: %s on %s record %s", action.value, table_name, record_id)
        return audit
    except Exception as e:
        logger.error("Error creating audit log: %s", e)
        raise


def audit_insert(
    db: Session,
    model: Any,
    user_id: Optional[str] = None,
    ip_address: Optional[str] = None,
) -> AuditLog:
    """
    Registra uma inserção no log de auditoria.

    Args:
        db: Sessão do banco de dados
        model: Instância do modelo criado
        user_id: ID do usuário que realizou a ação
        ip_address: Endereço IP de origem

    Returns:
        AuditLog: Registro de auditoria criado
    """
    table_name = model.__tablename__
    record_id = str(model.id)
    new_values = model_to_dict(model)

    return create_audit_log(
        db=db,
        table_name=table_name,
        record_id=record_id,
        action=AuditAction.INSERT,
        new_values=new_values,
        user_id=user_id,
        ip_address=ip_address,
    )


def audit_update(
    db: Session,
    model: Any,
    old_values: Dict[str, Any],
    user_id: Optional[str] = None,
    ip_address: Optional[str] = None,
) -> AuditLog:
    """
    Registra uma atualização no log de auditoria.

    Args:
        db: Sessão do banco de dados
        model: Instância do modelo atualizado
        old_values: Valores antigos antes da atualização
        user_id: ID do usuário que realizou a ação
        ip_address: Endereço IP de origem

    Returns:
        AuditLog: Registro de auditoria criado
    """
    table_name = model.__tablename__
    record_id = str(model.id)
    new_values = model_to_dict(model)

    return create_audit_log(
        db=db,
        table_name=table_name,
        record_id=record_id,
        action=AuditAction.UPDATE,
        old_values=old_values,
        new_values=new_values,
        user_id=user_id,
        ip_address=ip_address,
    )


def audit_delete(
    db: Session,
    model: Any,
    user_id: Optional[str] = None,
    ip_address: Optional[str] = None,
) -> AuditLog:
    """
    Registra uma exclusão no log de auditoria.

    Args:
        db: Sessão do banco de dados
        model: Instância do modelo excluído
        user_id: ID do usuário que realizou a ação
        ip_address: Endereço IP de origem

    Returns:
        AuditLog: Registro de auditoria criado
    """
    table_name = model.__tablename__
    record_id = str(model.id)
    old_values = model_to_dict(model)

    return create_audit_log(
        db=db,
        table_name=table_name,
        record_id=record_id,
        action=AuditAction.DELETE,
        old_values=old_values,
        user_id=user_id,
        ip_address=ip_address,
    )


def audit_equipment_status_change(
    db: Session,
    equipment: Any,
    old_status: str,
    new_status: str,
    user_id: Optional[str] = None,
    ip_address: Optional[str] = None,
) -> AuditLog:
    """
    Registra uma mudança de status de equipamento no log de auditoria.

    Args:
        db: Sessão do banco de dados
        equipment: Instância do equipamento
        old_status: Status antigo
        new_status: Novo status
        user_id: ID do usuário que realizou a ação
        ip_address: Endereço IP de origem

    Returns:
        AuditLog: Registro de auditoria criado
    """
    return create_audit_log(
        db=db,
        table_name="equipment",
        record_id=str(equipment.id),
        action=AuditAction.UPDATE,
        old_values={"status": old_status},
        new_values={"status": new_status},
        user_id=user_id,
        ip_address=ip_address,
    )
