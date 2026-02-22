import pytest
from datetime import datetime, timedelta, timezone
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from enums import EquipmentStatus, EventStatus, TransactionStatus, TransactionType
from models.equipment import Equipment
from models.event import Event
from models.transaction import Transaction


class TestListTransactions:
    def test_list_transactions_success(self, client: TestClient, auth_header: dict, sample_transaction: Transaction):
        response = client.get("/transactions/", headers=auth_header)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1

    def test_list_transactions_filter_by_type(self, client: TestClient, auth_header: dict, sample_transaction: Transaction):
        response = client.get("/transactions/?type=withdrawal", headers=auth_header)
        assert response.status_code == 200
        data = response.json()
        assert all(t["transaction_type"] == "withdrawal" for t in data)

    def test_list_transactions_filter_by_status(self, client: TestClient, auth_header: dict, sample_transaction: Transaction):
        response = client.get("/transactions/?status=completed", headers=auth_header)
        assert response.status_code == 200

    def test_list_transactions_unauthorized(self, client: TestClient):
        response = client.get("/transactions/")
        assert response.status_code == 401


class TestGetTransaction:
    def test_get_transaction_by_id_success(self, client: TestClient, auth_header: dict, sample_transaction: Transaction):
        response = client.get(f"/transactions/{sample_transaction.id}", headers=auth_header)
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == sample_transaction.id

    def test_get_transaction_by_id_not_found(self, client: TestClient, auth_header: dict):
        response = client.get("/transactions/nonexistent-id", headers=auth_header)
        assert response.status_code == 404


class TestCreateWithdrawal:
    def test_create_withdrawal_success(self, client: TestClient, auth_header: dict, sample_equipment: Equipment, sample_event: Event, admin_user):
        response = client.post(
            "/transactions/",
            headers=auth_header,
            json={
                "equipment_id": sample_equipment.id,
                "event_id": sample_event.id,
                "user_id": admin_user.id,
                "transaction_type": TransactionType.WITHDRAWAL,
                "scheduled_date": datetime.now(timezone.utc).isoformat(),
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["transaction_type"] == TransactionType.WITHDRAWAL

    def test_create_withdrawal_equipment_not_available(self, client: TestClient, auth_header: dict, sample_equipment_in_use: Equipment, sample_event: Event, admin_user):
        response = client.post(
            "/transactions/",
            headers=auth_header,
            json={
                "equipment_id": sample_equipment_in_use.id,
                "event_id": sample_event.id,
                "user_id": admin_user.id,
                "transaction_type": TransactionType.WITHDRAWAL,
                "scheduled_date": datetime.now(timezone.utc).isoformat(),
            },
        )
        assert response.status_code == 400
        assert "em uso" in response.json()["detail"]

    def test_create_withdrawal_event_not_found(self, client: TestClient, auth_header: dict, sample_equipment: Equipment, admin_user):
        response = client.post(
            "/transactions/",
            headers=auth_header,
            json={
                "equipment_id": sample_equipment.id,
                "event_id": "nonexistent-event",
                "user_id": admin_user.id,
                "transaction_type": TransactionType.WITHDRAWAL,
                "scheduled_date": datetime.now(timezone.utc).isoformat(),
            },
        )
        assert response.status_code == 404

    def test_create_withdrawal_equipment_not_found(self, client: TestClient, auth_header: dict, sample_event: Event, admin_user):
        response = client.post(
            "/transactions/",
            headers=auth_header,
            json={
                "equipment_id": "nonexistent-equipment",
                "event_id": sample_event.id,
                "user_id": admin_user.id,
                "transaction_type": TransactionType.WITHDRAWAL,
                "scheduled_date": datetime.now(timezone.utc).isoformat(),
            },
        )
        assert response.status_code == 404

    def test_create_withdrawal_updates_equipment_status(self, client: TestClient, auth_header: dict, sample_equipment: Equipment, sample_event: Event, admin_user, db: Session):
        response = client.post(
            "/transactions/",
            headers=auth_header,
            json={
                "equipment_id": sample_equipment.id,
                "event_id": sample_event.id,
                "user_id": admin_user.id,
                "transaction_type": TransactionType.WITHDRAWAL,
                "scheduled_date": datetime.now(timezone.utc).isoformat(),
            },
        )
        assert response.status_code == 201
        db.refresh(sample_equipment)
        assert sample_equipment.status == EquipmentStatus.IN_USE


class TestCreateReturn:
    def test_create_return_success(self, client: TestClient, auth_header: dict, sample_event: Event, admin_user, db: Session):
        equipment = Equipment(
            code="RETURN-EQ-001",
            name="Equipment for Return",
            category="Microphone",
            status=EquipmentStatus.IN_USE,
        )
        db.add(equipment)
        db.commit()
        db.refresh(equipment)

        response = client.post(
            "/transactions/",
            headers=auth_header,
            json={
                "equipment_id": equipment.id,
                "event_id": sample_event.id,
                "user_id": admin_user.id,
                "transaction_type": TransactionType.RETURN,
                "scheduled_date": datetime.now(timezone.utc).isoformat(),
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["transaction_type"] == TransactionType.RETURN

    def test_create_return_equipment_not_in_use(self, client: TestClient, auth_header: dict, sample_equipment: Equipment, sample_event: Event, admin_user):
        response = client.post(
            "/transactions/",
            headers=auth_header,
            json={
                "equipment_id": sample_equipment.id,
                "event_id": sample_event.id,
                "user_id": admin_user.id,
                "transaction_type": TransactionType.RETURN,
                "scheduled_date": datetime.now(timezone.utc).isoformat(),
            },
        )
        assert response.status_code == 400
        assert "not currently in use" in response.json()["detail"]

    def test_create_return_updates_equipment_status(self, client: TestClient, auth_header: dict, sample_event: Event, admin_user, db: Session):
        equipment = Equipment(
            code="RETURN-EQ-002",
            name="Equipment for Return 2",
            category="Microphone",
            status=EquipmentStatus.IN_USE,
        )
        db.add(equipment)
        db.commit()
        db.refresh(equipment)

        response = client.post(
            "/transactions/",
            headers=auth_header,
            json={
                "equipment_id": equipment.id,
                "event_id": sample_event.id,
                "user_id": admin_user.id,
                "transaction_type": TransactionType.RETURN,
                "scheduled_date": datetime.now(timezone.utc).isoformat(),
            },
        )
        assert response.status_code == 201
        db.refresh(equipment)
        assert equipment.status == EquipmentStatus.AVAILABLE


class TestUpdateTransaction:
    def test_update_transaction_success(self, client: TestClient, auth_header: dict, sample_transaction: Transaction):
        response = client.put(
            f"/transactions/{sample_transaction.id}",
            headers=auth_header,
            json={"notes": "Updated notes"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["notes"] == "Updated notes"

    def test_update_transaction_not_found(self, client: TestClient, auth_header: dict):
        response = client.put(
            "/transactions/nonexistent-id",
            headers=auth_header,
            json={"notes": "Updated"},
        )
        assert response.status_code == 404


class TestCancelTransaction:
    def test_cancel_transaction_success(self, client: TestClient, auth_header: dict, db: Session, sample_event: Event, admin_user, sample_equipment: Equipment):
        transaction = Transaction(
            equipment_id=sample_equipment.id,
            event_id=sample_event.id,
            user_id=admin_user.id,
            transaction_type=TransactionType.WITHDRAWAL,
            scheduled_date=datetime.now(timezone.utc),
            status=TransactionStatus.PENDING,
        )
        db.add(transaction)
        db.commit()
        db.refresh(transaction)

        response = client.delete(f"/transactions/{transaction.id}", headers=auth_header)
        assert response.status_code == 204
        db.refresh(transaction)
        assert transaction.status == TransactionStatus.CANCELLED

    def test_cancel_completed_transaction_forbidden(self, client: TestClient, auth_header: dict, sample_transaction: Transaction):
        response = client.delete(f"/transactions/{sample_transaction.id}", headers=auth_header)
        assert response.status_code == 400
