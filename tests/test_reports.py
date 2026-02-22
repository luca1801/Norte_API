import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from models.equipment import Equipment
from models.event import Event
from models.transaction import Transaction
from models.user import User


class TestDashboardStats:
    def test_get_dashboard_stats_success(self, client: TestClient, auth_header: dict, sample_equipment: Equipment, sample_event: Event):
        response = client.get("/reports/dashboard", headers=auth_header)
        assert response.status_code == 200
        data = response.json()
        assert "equipment" in data
        assert "events" in data
        assert "transactions" in data
        assert "users" in data

    def test_dashboard_equipment_stats(self, client: TestClient, auth_header: dict, sample_equipment: Equipment):
        response = client.get("/reports/dashboard", headers=auth_header)
        assert response.status_code == 200
        data = response.json()
        assert "total" in data["equipment"]
        assert "available" in data["equipment"]
        assert "in_use" in data["equipment"]
        assert "maintenance" in data["equipment"]

    def test_dashboard_user_stats(self, client: TestClient, auth_header: dict, admin_user: User):
        response = client.get("/reports/dashboard", headers=auth_header)
        assert response.status_code == 200
        data = response.json()
        assert "total" in data["users"]
        assert "active" in data["users"]

    def test_get_dashboard_stats_unauthorized(self, client: TestClient):
        response = client.get("/reports/dashboard")
        assert response.status_code == 401


class TestEquipmentUsageReport:
    def test_get_equipment_usage_success(self, client: TestClient, auth_header: dict, sample_equipment: Equipment):
        response = client.get("/reports/equipment-usage", headers=auth_header)
        assert response.status_code == 200
        data = response.json()
        assert "by_category" in data
        assert "by_status" in data

    def test_equipment_usage_by_category(self, client: TestClient, auth_header: dict, multiple_equipment: list[Equipment]):
        response = client.get("/reports/equipment-usage", headers=auth_header)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data["by_category"], list)
        assert len(data["by_category"]) >= 1

    def test_equipment_usage_by_status(self, client: TestClient, auth_header: dict, multiple_equipment: list[Equipment]):
        response = client.get("/reports/equipment-usage", headers=auth_header)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data["by_status"], list)
        assert len(data["by_status"]) >= 1

    def test_get_equipment_usage_unauthorized(self, client: TestClient):
        response = client.get("/reports/equipment-usage")
        assert response.status_code == 401


class TestAuditLog:
    def test_get_audit_log_admin_success(self, client: TestClient, auth_header: dict):
        response = client.get("/reports/audit-log", headers=auth_header)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_get_audit_log_operator_forbidden(self, client: TestClient, operator_auth_header: dict):
        response = client.get("/reports/audit-log", headers=operator_auth_header)
        assert response.status_code == 403

    def test_get_audit_log_unauthorized(self, client: TestClient):
        response = client.get("/reports/audit-log")
        assert response.status_code == 401


class TestAuditLogSummary:
    def test_get_audit_log_summary_admin_success(self, client: TestClient, auth_header: dict):
        response = client.get("/reports/audit-log/summary", headers=auth_header)
        assert response.status_code == 200
        data = response.json()
        assert "total" in data
        assert "by_action" in data
        assert "by_table" in data

    def test_get_audit_log_summary_operator_forbidden(self, client: TestClient, operator_auth_header: dict):
        response = client.get("/reports/audit-log/summary", headers=operator_auth_header)
        assert response.status_code == 403

    def test_get_audit_log_summary_unauthorized(self, client: TestClient):
        response = client.get("/reports/audit-log/summary")
        assert response.status_code == 401
