"""
Database configuration and session management.
"""

from sqlalchemy import create_engine, event
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from core.config import settings

# Create SQLAlchemy engine for SQLite
engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in settings.DATABASE_URL else {},
    echo=settings.LOG_LEVEL == "DEBUG",  # Log SQL queries in debug mode
)

# Enable foreign key support for SQLite
if "sqlite" in settings.DATABASE_URL:

    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        """Enable foreign key support for SQLite."""
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


# Create SessionLocal class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create Base class for models
Base = declarative_base()


def get_db():
    """Dependency to get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Initialize database tables."""
    # Import all models to ensure they are registered
    from models import AuditLog, Bag, Equipment, Event, Reservation, Transaction, User  # noqa: F401

    Base.metadata.create_all(bind=engine)

    # Create default data if not exists
    from datetime import datetime, timedelta, timezone

    from core.security import get_password_hash
    from enums import EquipmentCondition, EquipmentStatus, EventStatus, UserRole
    from utils.datetime_utils import now_brasilia, BRASILIA_TZ

    db = SessionLocal()
    try:
        # Check if data already exists
        admin_user = db.query(User).filter(User.username == "admin").first()
        existing_bag = db.query(Bag).first()

        if admin_user or existing_bag:
            db.close()
            return

        # ===== CREATE ADMIN USER =====
        admin_user = User(
            username="admin",
            email="admin@example.com",
            password_hash=get_password_hash("admin"),
            role=UserRole.ADMIN,
            is_active=True,
        )
        db.add(admin_user)

        # ===== CREATE 2 NORMAL USERS =====
        user1 = User(
            username="joao.silva",
            email="joao.silva@empresa.com",
            password_hash=get_password_hash("12345678"),
            role=UserRole.OPERATOR,
            is_active=True,
        )
        user2 = User(
            username="maria.santos",
            email="maria.santos@empresa.com",
            password_hash=get_password_hash("12345678"),
            role=UserRole.OPERATOR,
            is_active=True,
        )
        db.add_all([user1, user2])

        # ===== CREATE 4 BAGS =====
        bag1 = Bag(
            code="BAG-MIC-01",
            name="Kit Microfones Vocais",
            description="Conjunto de microfones para vocais",
        )
        bag2 = Bag(code="BAG-CAB-01", name="Kit Cabos XLR", description="Cabos XLR de 10m e 5m")
        bag3 = Bag(code="BAG-MON-01", name="Kit Monitores", description="Monitores de palco")
        bag4 = Bag(
            code="BAG-DI-01", name="Kit Direct Box", description="Direct boxes ativas e passivas"
        )
        db.add_all([bag1, bag2, bag3, bag4])
        db.flush()  # Para obter os IDs das bags

        # ===== CREATE 10 EQUIPMENTS =====
        equipments = [
            Equipment(
                code="MIC-SM58-001",
                name="Shure SM58",
                category="Microfone",
                status=EquipmentStatus.AVAILABLE,
                condition=EquipmentCondition.EXCELLENT,
                location="Estoque A",
                description="Microfone dinâmico vocal",
                bag_id=bag1.id,
            ),
            Equipment(
                code="MIC-SM58-002",
                name="Shure SM58",
                category="Microfone",
                status=EquipmentStatus.AVAILABLE,
                condition=EquipmentCondition.GOOD,
                location="Estoque A",
                description="Microfone dinâmico vocal",
                bag_id=bag1.id,
            ),
            Equipment(
                code="MIC-BETA58-001",
                name="Shure Beta 58A",
                category="Microfone",
                status=EquipmentStatus.AVAILABLE,
                condition=EquipmentCondition.EXCELLENT,
                location="Estoque A",
                description="Microfone dinâmico supercardioide",
            ),
            Equipment(
                code="MIX-X32-001",
                name="Behringer X32",
                category="Mesa de Som",
                status=EquipmentStatus.AVAILABLE,
                condition=EquipmentCondition.GOOD,
                location="Estoque B",
                description="Mesa digital 32 canais",
            ),
            Equipment(
                code="CAB-XLR-10M-001",
                name="Cabo XLR 10m",
                category="Cabo",
                status=EquipmentStatus.AVAILABLE,
                condition=EquipmentCondition.GOOD,
                location="Estoque C",
                description="Cabo XLR balanceado 10 metros",
                bag_id=bag2.id,
            ),
            Equipment(
                code="CAB-XLR-10M-002",
                name="Cabo XLR 10m",
                category="Cabo",
                status=EquipmentStatus.AVAILABLE,
                condition=EquipmentCondition.FAIR,
                location="Estoque C",
                description="Cabo XLR balanceado 10 metros",
                bag_id=bag2.id,
            ),
            Equipment(
                code="MON-QSC-001",
                name="QSC K12.2",
                category="Monitor",
                status=EquipmentStatus.MAINTENANCE,
                condition=EquipmentCondition.FAIR,
                location="Manutenção",
                description="Monitor ativo 12 polegadas",
                bag_id=bag3.id,
            ),
            Equipment(
                code="MON-QSC-002",
                name="QSC K12.2",
                category="Monitor",
                status=EquipmentStatus.AVAILABLE,
                condition=EquipmentCondition.GOOD,
                location="Estoque B",
                description="Monitor ativo 12 polegadas",
                bag_id=bag3.id,
            ),
            Equipment(
                code="DI-BSS-001",
                name="BSS AR-133",
                category="Direct Box",
                status=EquipmentStatus.AVAILABLE,
                condition=EquipmentCondition.EXCELLENT,
                location="Estoque A",
                description="Direct box ativa",
                bag_id=bag4.id,
            ),
            Equipment(
                code="AMP-CROWN-001",
                name="Crown XTi 4002",
                category="Amplificador",
                status=EquipmentStatus.AVAILABLE,
                condition=EquipmentCondition.GOOD,
                location="Estoque B",
                description="Amplificador de potência 2x1200W",
            ),
        ]
        db.add_all(equipments)

        # ===== CREATE 3 EVENTS =====
        now = now_brasilia()  # Usa timezone de Brasília
        event1 = Event(
            code="EVT-2026-001",
            name="Show Rock in Rio",
            type="Show",
            category="Festival",
            status=EventStatus.PLANNED,
            start_date=now + timedelta(days=7),
            end_date=now + timedelta(days=7, hours=6),
            location="Parque Olímpico, Rio de Janeiro",
            description="Festival de música Rock in Rio 2026",
            owner_id=admin_user.id,
        )
        event2 = Event(
            code="EVT-2026-002",
            name="Casamento Silva & Santos",
            type="Casamento",
            category="Evento Social",
            status=EventStatus.CONFIRMED,
            start_date=now + timedelta(days=3),
            end_date=now + timedelta(days=3, hours=8),
            location="Espaço Villa Garden, São Paulo",
            description="Cerimônia e festa de casamento",
            owner_id=admin_user.id,
        )
        event3 = Event(
            code="EVT-2026-003",
            name="Conferência Tech Summit",
            type="Corporativo",
            category="Conferência",
            status=EventStatus.IN_PROGRESS,
            start_date=now - timedelta(hours=2),
            end_date=now + timedelta(hours=6),
            location="Centro de Convenções Anhembi, São Paulo",
            description="Evento corporativo de tecnologia",
            owner_id=admin_user.id,
        )
        db.add_all([event1, event2, event3])

        db.commit()
        print("=" * 50)
        print("SEED DATA CREATED SUCCESSFULLY!")
        print("=" * 50)
        print("Users:")
        print("  - admin / admin (Admin)")
        print("  - joao.silva / 12345678 (Operator)")
        print("  - maria.santos / 12345678 (Operator)")
        print("Bags: 4 created")
        print("Equipment: 10 created")
        print("Events: 3 created")
        print("=" * 50)

    except Exception as e:
        db.rollback()
        print(f"Error creating seed data: {e}")
        raise
    finally:
        db.close()
