import os
import sys
from datetime import datetime, timedelta, timezone
from typing import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker

TEST_DB_PATH = "/tmp/test_api_norte.db"
SQLALCHEMY_DATABASE_URL = f"sqlite:///{TEST_DB_PATH}"

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@pytest.fixture(scope="session", autouse=True)
def setup_test_database():
    if os.path.exists(TEST_DB_PATH):
        os.remove(TEST_DB_PATH)
    
    from core.database import Base
    from models.user import User
    from models.equipment import Equipment
    from models.event import Event
    from models.bag import Bag
    from models.transaction import Transaction
    from models.reservation import Reservation
    from models.audit_log import AuditLog
    
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL,
        connect_args={"check_same_thread": False},
    )
    
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()
    
    Base.metadata.create_all(bind=engine)
    
    from core import database
    database.engine = engine
    database.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    yield
    
    Base.metadata.drop_all(bind=engine)
    if os.path.exists(TEST_DB_PATH):
        os.remove(TEST_DB_PATH)


@pytest.fixture(scope="function")
def db() -> Generator[Session, None, None]:
    from core import database
    from core.database import Base
    
    session = database.SessionLocal()
    try:
        yield session
    finally:
        session.rollback()
        for table in reversed(Base.metadata.sorted_tables):
            session.execute(table.delete())
        session.commit()
        session.close()


@pytest.fixture(scope="function")
def client(db: Session) -> Generator[TestClient, None, None]:
    from main import app as main_app
    from core import database

    def override_get_db():
        try:
            yield db
        finally:
            pass

    main_app.dependency_overrides[database.get_db] = override_get_db
    yield TestClient(app=main_app, raise_server_exceptions=True)
    main_app.dependency_overrides.clear()


@pytest.fixture
def admin_user(db: Session):
    from core.security import get_password_hash
    from models.user import User
    from enums import UserRole
    
    user = User(
        username="testadmin",
        email="testadmin@example.com",
        password_hash=get_password_hash("admin123"),
        role=UserRole.ADMIN,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def operator_user(db: Session):
    from core.security import get_password_hash
    from models.user import User
    from enums import UserRole
    
    user = User(
        username="testoperator",
        email="testoperator@example.com",
        password_hash=get_password_hash("operator123"),
        role=UserRole.OPERATOR,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def inactive_user(db: Session):
    from core.security import get_password_hash
    from models.user import User
    from enums import UserRole
    
    user = User(
        username="inactiveuser",
        email="inactive@example.com",
        password_hash=get_password_hash("inactive123"),
        role=UserRole.OPERATOR,
        is_active=False,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def auth_header(admin_user):
    from core.security import create_access_token
    
    access_token = create_access_token(
        data={"sub": str(admin_user.id), "username": admin_user.username, "role": admin_user.role.value},
        expires_delta=timedelta(minutes=30),
    )
    return {"Authorization": f"Bearer {access_token}"}


@pytest.fixture
def operator_auth_header(operator_user):
    from core.security import create_access_token
    
    access_token = create_access_token(
        data={"sub": str(operator_user.id), "username": operator_user.username, "role": operator_user.role.value},
        expires_delta=timedelta(minutes=30),
    )
    return {"Authorization": f"Bearer {access_token}"}


@pytest.fixture
def sample_equipment(db: Session):
    from models.equipment import Equipment
    from enums import EquipmentStatus, EquipmentCondition
    
    equipment = Equipment(
        code="TEST-MIC-001",
        name="Test Microphone",
        category="Microphone",
        status=EquipmentStatus.AVAILABLE,
        condition=EquipmentCondition.GOOD,
        location="Test Location",
        description="Test equipment for testing",
    )
    db.add(equipment)
    db.commit()
    db.refresh(equipment)
    return equipment


@pytest.fixture
def sample_equipment_in_use(db: Session):
    from models.equipment import Equipment
    from enums import EquipmentStatus, EquipmentCondition
    
    equipment = Equipment(
        code="TEST-MIC-002",
        name="Test Microphone In Use",
        category="Microphone",
        status=EquipmentStatus.IN_USE,
        condition=EquipmentCondition.GOOD,
        location="Test Location",
        description="Test equipment in use",
    )
    db.add(equipment)
    db.commit()
    db.refresh(equipment)
    return equipment


@pytest.fixture
def sample_event(db: Session, admin_user):
    from models.event import Event
    from enums import EventStatus
    
    now = datetime.now(timezone.utc)
    event = Event(
        code="TEST-EVT-001",
        name="Test Event",
        type="Test",
        category="Test Category",
        status=EventStatus.PLANNED,
        start_date=now + timedelta(days=1),
        end_date=now + timedelta(days=1, hours=4),
        location="Test Location",
        description="Test event for testing",
        owner_id=admin_user.id,
    )
    db.add(event)
    db.commit()
    db.refresh(event)
    return event


@pytest.fixture
def sample_bag(db: Session):
    from models.bag import Bag
    
    bag = Bag(
        code="TEST-BAG-001",
        name="Test Bag",
        description="Test bag for testing",
    )
    db.add(bag)
    db.commit()
    db.refresh(bag)
    return bag


@pytest.fixture
def sample_transaction(db: Session, sample_equipment, sample_event, admin_user):
    from models.transaction import Transaction
    from enums import TransactionType, TransactionStatus
    
    transaction = Transaction(
        equipment_id=sample_equipment.id,
        event_id=sample_event.id,
        user_id=admin_user.id,
        transaction_type=TransactionType.WITHDRAWAL,
        scheduled_date=datetime.now(timezone.utc),
        status=TransactionStatus.COMPLETED,
    )
    db.add(transaction)
    db.commit()
    db.refresh(transaction)
    return transaction


@pytest.fixture
def sample_reservation(db: Session, sample_equipment, sample_event, admin_user):
    from models.reservation import Reservation
    from enums import ReservationStatus
    
    now = datetime.now(timezone.utc)
    reservation = Reservation(
        equipment_id=sample_equipment.id,
        event_id=sample_event.id,
        reserved_by=admin_user.id,
        start_date=now + timedelta(days=1),
        end_date=now + timedelta(days=2),
        status=ReservationStatus.ACTIVE,
    )
    db.add(reservation)
    db.commit()
    db.refresh(reservation)
    return reservation


@pytest.fixture
def multiple_equipment(db: Session):
    from models.equipment import Equipment
    from enums import EquipmentStatus, EquipmentCondition
    
    equipments = [
        Equipment(
            code=f"TEST-MIC-{i:03d}",
            name=f"Test Microphone {i}",
            category="Microphone" if i % 2 == 0 else "Cable",
            status=EquipmentStatus.AVAILABLE if i % 3 == 0 else EquipmentStatus.IN_USE,
            condition=EquipmentCondition.GOOD,
            location="Test Location",
        )
        for i in range(1, 6)
    ]
    db.add_all(equipments)
    db.commit()
    for eq in equipments:
        db.refresh(eq)
    return equipments
