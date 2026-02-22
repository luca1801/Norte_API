import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from enums import EquipmentCondition, EquipmentStatus
from models.equipment import Equipment


class TestListEquipment:
    def test_list_equipment_success(self, client: TestClient, auth_header: dict, sample_equipment: Equipment):
        response = client.get("/equipment/", headers=auth_header)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1

    def test_list_equipment_filter_by_category(self, client: TestClient, auth_header: dict, sample_equipment: Equipment):
        response = client.get("/equipment/?category=Microphone", headers=auth_header)
        assert response.status_code == 200
        data = response.json()
        assert all(eq["category"] == "Microphone" for eq in data)

    def test_list_equipment_filter_by_status(self, client: TestClient, auth_header: dict, sample_equipment: Equipment):
        response = client.get(f"/equipment/?status=available", headers=auth_header)
        assert response.status_code == 200
        data = response.json()
        assert all(eq["status"] == EquipmentStatus.AVAILABLE for eq in data)

    def test_list_equipment_pagination(self, client: TestClient, auth_header: dict, multiple_equipment: list[Equipment]):
        response = client.get("/equipment/?skip=0&limit=2", headers=auth_header)
        assert response.status_code == 200
        data = response.json()
        assert len(data) <= 2

    def test_list_equipment_unauthorized(self, client: TestClient):
        response = client.get("/equipment/")
        assert response.status_code == 401


class TestGetEquipment:
    def test_get_equipment_by_id_success(self, client: TestClient, auth_header: dict, sample_equipment: Equipment):
        response = client.get(f"/equipment/{sample_equipment.id}", headers=auth_header)
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == sample_equipment.id
        assert data["code"] == sample_equipment.code
        assert data["name"] == sample_equipment.name

    def test_get_equipment_by_id_not_found(self, client: TestClient, auth_header: dict):
        response = client.get("/equipment/nonexistent-id", headers=auth_header)
        assert response.status_code == 404

    def test_get_equipment_by_code_success(self, client: TestClient, auth_header: dict, sample_equipment: Equipment):
        response = client.get(f"/equipment/code/{sample_equipment.code}", headers=auth_header)
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == sample_equipment.code

    def test_get_equipment_by_code_not_found(self, client: TestClient, auth_header: dict):
        response = client.get("/equipment/code/NONEXISTENT", headers=auth_header)
        assert response.status_code == 404


class TestCreateEquipment:
    def test_create_equipment_admin_success(self, client: TestClient, auth_header: dict):
        response = client.post(
            "/equipment/",
            headers=auth_header,
            json={
                "code": "NEW-MIC-001",
                "name": "New Microphone",
                "category": "Microphone",
                "status": EquipmentStatus.AVAILABLE,
                "condition": EquipmentCondition.GOOD,
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["code"] == "NEW-MIC-001"
        assert data["name"] == "New Microphone"

    def test_create_equipment_duplicate_code(self, client: TestClient, auth_header: dict, sample_equipment: Equipment):
        response = client.post(
            "/equipment/",
            headers=auth_header,
            json={
                "code": sample_equipment.code,
                "name": "Duplicate Code",
                "category": "Microphone",
            },
        )
        assert response.status_code == 400
        assert "already exists" in response.json()["detail"]

    def test_create_equipment_operator_forbidden(self, client: TestClient, operator_auth_header: dict):
        response = client.post(
            "/equipment/",
            headers=operator_auth_header,
            json={
                "code": "NEW-MIC-002",
                "name": "New Microphone",
                "category": "Microphone",
            },
        )
        assert response.status_code == 403

    def test_create_equipment_unauthorized(self, client: TestClient):
        response = client.post(
            "/equipment/",
            json={
                "code": "NEW-MIC-003",
                "name": "New Microphone",
                "category": "Microphone",
            },
        )
        assert response.status_code == 401


class TestUpdateEquipment:
    def test_update_equipment_admin_success(self, client: TestClient, auth_header: dict, sample_equipment: Equipment):
        response = client.put(
            f"/equipment/{sample_equipment.id}",
            headers=auth_header,
            json={"name": "Updated Microphone", "location": "New Location"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Microphone"
        assert data["location"] == "New Location"

    def test_update_equipment_status(self, client: TestClient, auth_header: dict, sample_equipment: Equipment):
        response = client.put(
            f"/equipment/{sample_equipment.id}",
            headers=auth_header,
            json={"status": EquipmentStatus.MAINTENANCE},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == EquipmentStatus.MAINTENANCE

    def test_update_equipment_not_found(self, client: TestClient, auth_header: dict):
        response = client.put(
            "/equipment/nonexistent-id",
            headers=auth_header,
            json={"name": "Updated"},
        )
        assert response.status_code == 404

    def test_update_equipment_operator_forbidden(self, client: TestClient, operator_auth_header: dict, sample_equipment: Equipment):
        response = client.put(
            f"/equipment/{sample_equipment.id}",
            headers=operator_auth_header,
            json={"name": "Updated"},
        )
        assert response.status_code == 403


class TestDeleteEquipment:
    def test_delete_equipment_admin_success(self, client: TestClient, auth_header: dict, sample_equipment: Equipment, db: Session):
        response = client.delete(f"/equipment/{sample_equipment.id}", headers=auth_header)
        assert response.status_code == 204
        db.refresh(sample_equipment)
        assert sample_equipment.status == EquipmentStatus.EXCLUDED

    def test_delete_equipment_not_found(self, client: TestClient, auth_header: dict):
        response = client.delete("/equipment/nonexistent-id", headers=auth_header)
        assert response.status_code == 404

    def test_delete_equipment_operator_forbidden(self, client: TestClient, operator_auth_header: dict, sample_equipment: Equipment):
        response = client.delete(f"/equipment/{sample_equipment.id}", headers=operator_auth_header)
        assert response.status_code == 403
