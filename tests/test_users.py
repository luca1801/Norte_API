import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from enums import UserRole
from models.user import User


class TestGetCurrentUser:
    def test_get_current_user_success(self, client: TestClient, auth_header: dict, admin_user: User):
        response = client.get("/users/me", headers=auth_header)
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == admin_user.username
        assert data["email"] == admin_user.email
        assert data["role"] == UserRole.ADMIN

    def test_get_current_user_unauthorized(self, client: TestClient):
        response = client.get("/users/me")
        assert response.status_code == 401

    def test_get_current_user_invalid_token(self, client: TestClient):
        response = client.get("/users/me", headers={"Authorization": "Bearer invalid_token"})
        assert response.status_code == 401


class TestUpdateCurrentUser:
    def test_update_current_user_username(self, client: TestClient, auth_header: dict):
        response = client.put(
            "/users/me",
            headers=auth_header,
            json={"username": "newusername"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "newusername"

    def test_update_current_user_email(self, client: TestClient, auth_header: dict):
        response = client.put(
            "/users/me",
            headers=auth_header,
            json={"email": "newemail@example.com"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "newemail@example.com"

    def test_update_current_user_password(self, client: TestClient, auth_header: dict, admin_user: User, db: Session):
        response = client.put(
            "/users/me",
            headers=auth_header,
            json={"password": "newpassword123"},
        )
        assert response.status_code == 200
        db.refresh(admin_user)
        from core.security import verify_password
        assert verify_password("newpassword123", admin_user.password_hash)

    def test_update_current_user_unauthorized(self, client: TestClient):
        response = client.put("/users/me", json={"username": "newusername"})
        assert response.status_code == 401


class TestListUsersPublic:
    def test_list_users_public_success(self, client: TestClient, auth_header: dict, admin_user: User):
        response = client.get("/users/public", headers=auth_header)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1

    def test_list_users_public_unauthorized(self, client: TestClient):
        response = client.get("/users/public")
        assert response.status_code == 401


class TestListUsers:
    def test_list_users_admin_success(self, client: TestClient, auth_header: dict, admin_user: User, operator_user: User):
        response = client.get("/users/", headers=auth_header)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 2

    def test_list_users_operator_forbidden(self, client: TestClient, operator_auth_header: dict):
        response = client.get("/users/", headers=operator_auth_header)
        assert response.status_code == 403

    def test_list_users_unauthorized(self, client: TestClient):
        response = client.get("/users/")
        assert response.status_code == 401


class TestGetUserById:
    def test_get_user_by_id_admin_success(self, client: TestClient, auth_header: dict, operator_user: User):
        response = client.get(f"/users/{operator_user.id}", headers=auth_header)
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == operator_user.id
        assert data["username"] == operator_user.username

    def test_get_user_by_id_not_found(self, client: TestClient, auth_header: dict):
        response = client.get("/users/nonexistent-id", headers=auth_header)
        assert response.status_code == 404

    def test_get_user_by_id_operator_forbidden(self, client: TestClient, operator_auth_header: dict, admin_user: User):
        response = client.get(f"/users/{admin_user.id}", headers=operator_auth_header)
        assert response.status_code == 403


class TestUpdateUser:
    def test_update_user_admin_success(self, client: TestClient, auth_header: dict, operator_user: User):
        response = client.put(
            f"/users/{operator_user.id}",
            headers=auth_header,
            json={"role": UserRole.MANAGER},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["role"] == UserRole.MANAGER

    def test_update_user_admin_deactivate(self, client: TestClient, auth_header: dict, operator_user: User):
        response = client.put(
            f"/users/{operator_user.id}",
            headers=auth_header,
            json={"is_active": False},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["is_active"] is False

    def test_update_user_not_found(self, client: TestClient, auth_header: dict):
        response = client.put(
            "/users/nonexistent-id",
            headers=auth_header,
            json={"role": UserRole.MANAGER},
        )
        assert response.status_code == 404

    def test_update_user_operator_forbidden(self, client: TestClient, operator_auth_header: dict, admin_user: User):
        response = client.put(
            f"/users/{admin_user.id}",
            headers=operator_auth_header,
            json={"role": UserRole.OPERATOR},
        )
        assert response.status_code == 403


class TestDeleteUser:
    def test_delete_user_admin_success(self, client: TestClient, auth_header: dict, operator_user: User, db: Session):
        response = client.delete(f"/users/{operator_user.id}", headers=auth_header)
        assert response.status_code == 204
        db.refresh(operator_user)
        assert operator_user.is_active is False

    def test_delete_user_not_found(self, client: TestClient, auth_header: dict):
        response = client.delete("/users/nonexistent-id", headers=auth_header)
        assert response.status_code == 404

    def test_delete_user_operator_forbidden(self, client: TestClient, operator_auth_header: dict, admin_user: User):
        response = client.delete(f"/users/{admin_user.id}", headers=operator_auth_header)
        assert response.status_code == 403
