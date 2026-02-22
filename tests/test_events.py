import pytest
from datetime import datetime, timedelta, timezone
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from enums import EventStatus
from models.event import Event
from models.user import User


class TestListEvents:
    def test_list_events_success(self, client: TestClient, auth_header: dict, sample_event: Event):
        response = client.get("/events/", headers=auth_header)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1

    def test_list_events_filter_by_status(self, client: TestClient, auth_header: dict, sample_event: Event):
        response = client.get("/events/?status=planned", headers=auth_header)
        assert response.status_code == 200
        data = response.json()
        assert all(ev["status"] == EventStatus.PLANNED for ev in data)

    def test_list_events_pagination(self, client: TestClient, auth_header: dict, db: Session, admin_user: User):
        now = datetime.now(timezone.utc)
        for i in range(5):
            event = Event(
                code=f"PAG-EVT-{i:03d}",
                name=f"Pagination Event {i}",
                type="Test",
                status=EventStatus.PLANNED,
                start_date=now + timedelta(days=i + 1),
                end_date=now + timedelta(days=i + 1, hours=4),
                owner_id=admin_user.id,
            )
            db.add(event)
        db.commit()

        response = client.get("/events/?skip=0&limit=2", headers=auth_header)
        assert response.status_code == 200
        data = response.json()
        assert len(data) <= 2

    def test_list_events_unauthorized(self, client: TestClient):
        response = client.get("/events/")
        assert response.status_code == 401


class TestGetEvent:
    def test_get_event_by_id_success(self, client: TestClient, auth_header: dict, sample_event: Event):
        response = client.get(f"/events/{sample_event.id}", headers=auth_header)
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == sample_event.id
        assert data["code"] == sample_event.code
        assert data["name"] == sample_event.name

    def test_get_event_by_id_not_found(self, client: TestClient, auth_header: dict):
        response = client.get("/events/nonexistent-id", headers=auth_header)
        assert response.status_code == 404

    def test_get_event_by_code_success(self, client: TestClient, auth_header: dict, sample_event: Event):
        response = client.get(f"/events/code/{sample_event.code}", headers=auth_header)
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == sample_event.code

    def test_get_event_by_code_not_found(self, client: TestClient, auth_header: dict):
        response = client.get("/events/code/NONEXISTENT", headers=auth_header)
        assert response.status_code == 404


class TestCreateEvent:
    def test_create_event_success(self, client: TestClient, auth_header: dict, admin_user: User):
        now = datetime.now(timezone.utc)
        response = client.post(
            "/events/",
            headers=auth_header,
            json={
                "code": "NEW-EVT-001",
                "name": "New Event",
                "type": "Concert",
                "category": "Music",
                "start_date": (now + timedelta(days=10)).isoformat(),
                "end_date": (now + timedelta(days=10, hours=6)).isoformat(),
                "location": "Test Venue",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["code"] == "NEW-EVT-001"
        assert data["name"] == "New Event"

    def test_create_event_duplicate_code(self, client: TestClient, auth_header: dict, sample_event: Event):
        now = datetime.now(timezone.utc)
        response = client.post(
            "/events/",
            headers=auth_header,
            json={
                "code": sample_event.code,
                "name": "Duplicate Event",
                "type": "Test",
                "start_date": (now + timedelta(days=10)).isoformat(),
                "end_date": (now + timedelta(days=10, hours=4)).isoformat(),
            },
        )
        assert response.status_code == 400

    def test_create_event_invalid_dates(self, client: TestClient, auth_header: dict):
        now = datetime.now(timezone.utc)
        response = client.post(
            "/events/",
            headers=auth_header,
            json={
                "code": "INVALID-EVT",
                "name": "Invalid Event",
                "type": "Test",
                "start_date": (now + timedelta(days=10)).isoformat(),
                "end_date": (now + timedelta(days=5)).isoformat(),
            },
        )
        assert response.status_code == 422


class TestUpdateEvent:
    def test_update_event_success(self, client: TestClient, auth_header: dict, sample_event: Event):
        response = client.put(
            f"/events/{sample_event.id}",
            headers=auth_header,
            json={"name": "Updated Event", "location": "Updated Location"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Event"
        assert data["location"] == "Updated Location"

    def test_update_event_status(self, client: TestClient, auth_header: dict, sample_event: Event):
        response = client.put(
            f"/events/{sample_event.id}",
            headers=auth_header,
            json={"status": EventStatus.CONFIRMED},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == EventStatus.CONFIRMED

    def test_update_event_not_found(self, client: TestClient, auth_header: dict):
        response = client.put(
            "/events/nonexistent-id",
            headers=auth_header,
            json={"name": "Updated"},
        )
        assert response.status_code == 404


class TestDeleteEvent:
    def test_delete_event_success(self, client: TestClient, auth_header: dict, sample_event: Event, db: Session):
        response = client.delete(f"/events/{sample_event.id}", headers=auth_header)
        assert response.status_code == 204

    def test_delete_event_not_found(self, client: TestClient, auth_header: dict):
        response = client.delete("/events/nonexistent-id", headers=auth_header)
        assert response.status_code == 404
