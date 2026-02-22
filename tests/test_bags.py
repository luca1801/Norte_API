import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from enums import EquipmentStatus
from models.bag import Bag
from models.equipment import Equipment


class TestListBags:
    def test_list_bags_success(self, client: TestClient, auth_header: dict, sample_bag: Bag):
        response = client.get("/bags/", headers=auth_header)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1

    def test_list_bags_unauthorized(self, client: TestClient):
        response = client.get("/bags/")
        assert response.status_code == 401


class TestGetBag:
    def test_get_bag_by_id_success(self, client: TestClient, auth_header: dict, sample_bag: Bag):
        response = client.get(f"/bags/{sample_bag.id}", headers=auth_header)
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == sample_bag.id
        assert data["code"] == sample_bag.code

    def test_get_bag_by_id_not_found(self, client: TestClient, auth_header: dict):
        response = client.get("/bags/nonexistent-id", headers=auth_header)
        assert response.status_code == 404

    def test_get_bag_with_equipment(self, client: TestClient, auth_header: dict, sample_bag: Bag, db: Session):
        equipment = Equipment(
            code="BAG-EQ-001",
            name="Equipment in Bag",
            category="Microphone",
            status=EquipmentStatus.AVAILABLE,
            bag_id=sample_bag.id,
        )
        db.add(equipment)
        db.commit()

        response = client.get(f"/bags/{sample_bag.id}", headers=auth_header)
        assert response.status_code == 200


class TestCreateBag:
    def test_create_bag_admin_success(self, client: TestClient, auth_header: dict):
        response = client.post(
            "/bags/",
            headers=auth_header,
            json={
                "code": "NEW-BAG-001",
                "name": "New Bag",
                "description": "New bag for testing",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["code"] == "NEW-BAG-001"
        assert data["name"] == "New Bag"

    def test_create_bag_duplicate_code(self, client: TestClient, auth_header: dict, sample_bag: Bag):
        response = client.post(
            "/bags/",
            headers=auth_header,
            json={
                "code": sample_bag.code,
                "name": "Duplicate Bag",
            },
        )
        assert response.status_code == 400

    def test_create_bag_operator_forbidden(self, client: TestClient, operator_auth_header: dict):
        response = client.post(
            "/bags/",
            headers=operator_auth_header,
            json={
                "code": "NEW-BAG-002",
                "name": "New Bag",
            },
        )
        assert response.status_code == 403


class TestUpdateBag:
    def test_update_bag_admin_success(self, client: TestClient, auth_header: dict, sample_bag: Bag):
        response = client.put(
            f"/bags/{sample_bag.id}",
            headers=auth_header,
            json={"name": "Updated Bag", "description": "Updated description"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Bag"

    def test_update_bag_not_found(self, client: TestClient, auth_header: dict):
        response = client.put(
            "/bags/nonexistent-id",
            headers=auth_header,
            json={"name": "Updated"},
        )
        assert response.status_code == 404


class TestDeleteBag:
    def test_delete_bag_success(self, client: TestClient, auth_header: dict, sample_bag: Bag, db: Session):
        response = client.delete(f"/bags/{sample_bag.id}", headers=auth_header)
        assert response.status_code == 204

    def test_delete_bag_not_found(self, client: TestClient, auth_header: dict):
        response = client.delete("/bags/nonexistent-id", headers=auth_header)
        assert response.status_code == 404


class TestBagEquipmentRelation:
    def test_add_equipment_to_bag(self, client: TestClient, auth_header: dict, sample_bag: Bag, sample_equipment: Equipment, db: Session):
        response = client.put(
            f"/equipment/{sample_equipment.id}",
            headers=auth_header,
            json={"bag_id": sample_bag.id},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["bag_id"] == sample_bag.id

    def test_remove_equipment_from_bag(self, client: TestClient, auth_header: dict, sample_bag: Bag, db: Session):
        equipment = Equipment(
            code="BAG-EQ-002",
            name="Equipment to Remove",
            category="Microphone",
            status=EquipmentStatus.AVAILABLE,
            bag_id=sample_bag.id,
        )
        db.add(equipment)
        db.commit()
        db.refresh(equipment)

        response = client.put(
            f"/equipment/{equipment.id}",
            headers=auth_header,
            json={"bag_id": None},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["bag_id"] is None
