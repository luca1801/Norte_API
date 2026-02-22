import pytest
from datetime import datetime, timedelta, timezone
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from enums import ReservationStatus
from models.reservation import Reservation
from models.equipment import Equipment


class TestListReservations:
    def test_list_reservations_success(self, client: TestClient, auth_header: dict, sample_reservation: Reservation):
        response = client.get("/reservations/", headers=auth_header)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1

    def test_list_reservations_filter_by_status(self, client: TestClient, auth_header: dict, sample_reservation: Reservation):
        response = client.get("/reservations/?status=active", headers=auth_header)
        assert response.status_code == 200
        data = response.json()
        assert all(r["status"] == ReservationStatus.ACTIVE for r in data)

    def test_list_reservations_unauthorized(self, client: TestClient):
        response = client.get("/reservations/")
        assert response.status_code == 401


class TestGetReservation:
    def test_get_reservation_by_id_success(self, client: TestClient, auth_header: dict, sample_reservation: Reservation):
        response = client.get(f"/reservations/{sample_reservation.id}", headers=auth_header)
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == sample_reservation.id

    def test_get_reservation_by_id_not_found(self, client: TestClient, auth_header: dict):
        response = client.get("/reservations/nonexistent-id", headers=auth_header)
        assert response.status_code == 404


class TestCreateReservation:
    def test_create_reservation_success(self, client: TestClient, auth_header: dict, admin_user, db: Session):
        from models.equipment import Equipment
        from models.event import Event
        from enums import EquipmentStatus, EquipmentCondition, EventStatus
        
        equipment = Equipment(
            code="NEW-RES-EQ-001",
            name="Equipment for Reservation",
            category="Microphone",
            status=EquipmentStatus.AVAILABLE,
            condition=EquipmentCondition.GOOD,
        )
        db.add(equipment)
        
        now = datetime.now(timezone.utc)
        event = Event(
            code="NEW-RES-EVT-001",
            name="Event for Reservation",
            type="Test",
            status=EventStatus.CONFIRMED,
            start_date=now + timedelta(days=1),
            end_date=now + timedelta(days=2),
            owner_id=admin_user.id,
        )
        db.add(event)
        db.commit()
        db.refresh(equipment)
        db.refresh(event)
        
        response = client.post(
            "/reservations/",
            headers=auth_header,
            json={
                "equipment_id": equipment.id,
                "event_id": event.id,
                "reserved_by": admin_user.id,
                "start_date": (now + timedelta(days=5)).isoformat(),
                "end_date": (now + timedelta(days=6)).isoformat(),
            },
        )
        if response.status_code != 201:
            print(f"Response: {response.status_code} - {response.json()}")
        assert response.status_code == 201
        data = response.json()
        assert data["equipment_id"] == equipment.id

    def test_create_reservation_invalid_dates(self, client: TestClient, auth_header: dict, sample_equipment: Equipment, sample_event, admin_user):
        now = datetime.now(timezone.utc)
        response = client.post(
            "/reservations/",
            headers=auth_header,
            json={
                "equipment_id": sample_equipment.id,
                "event_id": sample_event.id,
                "reserved_by": admin_user.id,
                "start_date": (now + timedelta(days=6)).isoformat(),
                "end_date": (now + timedelta(days=5)).isoformat(),
            },
        )
        assert response.status_code == 422

    def test_create_reservation_event_not_found(self, client: TestClient, auth_header: dict, sample_equipment: Equipment, admin_user):
        now = datetime.now(timezone.utc)
        response = client.post(
            "/reservations/",
            headers=auth_header,
            json={
                "equipment_id": sample_equipment.id,
                "event_id": "nonexistent-event",
                "reserved_by": admin_user.id,
                "start_date": (now + timedelta(days=5)).isoformat(),
                "end_date": (now + timedelta(days=6)).isoformat(),
            },
        )
        assert response.status_code == 404


class TestUpdateReservation:
    def test_update_reservation_success(self, client: TestClient, auth_header: dict, sample_reservation: Reservation):
        now = datetime.now(timezone.utc)
        response = client.put(
            f"/reservations/{sample_reservation.id}",
            headers=auth_header,
            json={
                "start_date": (now + timedelta(days=10)).isoformat(),
                "end_date": (now + timedelta(days=11)).isoformat(),
            },
        )
        assert response.status_code == 200

    def test_update_reservation_status(self, client: TestClient, auth_header: dict, sample_reservation: Reservation):
        response = client.put(
            f"/reservations/{sample_reservation.id}",
            headers=auth_header,
            json={"status": ReservationStatus.CANCELLED},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == ReservationStatus.CANCELLED

    def test_update_reservation_not_found(self, client: TestClient, auth_header: dict):
        now = datetime.now(timezone.utc)
        response = client.put(
            "/reservations/nonexistent-id",
            headers=auth_header,
            json={
                "start_date": (now + timedelta(days=10)).isoformat(),
                "end_date": (now + timedelta(days=11)).isoformat(),
            },
        )
        assert response.status_code == 404


class TestDeleteReservation:
    def test_delete_reservation_success(self, client: TestClient, auth_header: dict, sample_reservation: Reservation, db: Session):
        response = client.delete(f"/reservations/{sample_reservation.id}", headers=auth_header)
        assert response.status_code == 204

    def test_delete_reservation_not_found(self, client: TestClient, auth_header: dict):
        response = client.delete("/reservations/nonexistent-id", headers=auth_header)
        assert response.status_code == 404
