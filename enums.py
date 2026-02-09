"""
Enums para o sistema de gerenciamento de ativos.
Define todos os tipos enumerados usados nos modelos e schemas.
"""

from enum import Enum


class UserRole(str, Enum):
    """Roles de usuário do sistema."""

    ADMIN = "admin"
    MANAGER = "manager"
    OPERATOR = "operator"
    VIEWER = "viewer"


class EquipmentStatus(str, Enum):
    """Status de um equipamento."""

    AVAILABLE = "available"
    RESERVED = "reserved"
    IN_USE = "in_use"
    MAINTENANCE = "maintenance"
    EXCLUDED = "excluded"


class EquipmentCondition(str, Enum):
    """Condição física de um equipamento."""

    EXCELLENT = "excellent"
    GOOD = "good"
    FAIR = "fair"
    POOR = "poor"
    DAMAGED = "damaged"


class BagStatus(str, Enum):
    """Status de uma bag."""

    AVAILABLE = "available"
    RESERVED = "reserved"
    IN_USE = "in_use"
    EXCLUDED = "excluded"


class EventStatus(str, Enum):
    """Status de um evento."""

    PLANNED = "planned"
    CONFIRMED = "confirmed"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class TransactionType(str, Enum):
    """Tipo de transação (retirada ou devolução)."""

    WITHDRAWAL = "withdrawal"
    RETURN = "return"


class TransactionStatus(str, Enum):
    """Status de uma transação."""

    PENDING = "pending"
    CONFIRMED = "confirmed"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class ReservationStatus(str, Enum):
    """Status de uma reserva."""

    ACTIVE = "active"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class AuditAction(str, Enum):
    """Ações registradas no log de auditoria."""

    INSERT = "INSERT"
    UPDATE = "UPDATE"
    DELETE = "DELETE"
