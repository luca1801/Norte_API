import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from core.security import get_password_hash
from enums import UserRole
from models.user import User


class TestRegister:
    def test_register_success(self, client: TestClient, db: Session):
        response = client.post(
            "/auth/register",
            json={
                "username": "newuser",
                "email": "newuser@example.com",
                "password": "password123",
                "role": UserRole.OPERATOR,
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["username"] == "newuser"
        assert data["email"] == "newuser@example.com"
        assert data["role"] == UserRole.OPERATOR
        assert "id" in data

    def test_register_duplicate_username(self, client: TestClient, admin_user: User):
        response = client.post(
            "/auth/register",
            json={
                "username": admin_user.username,
                "email": "different@example.com",
                "password": "password123",
                "role": UserRole.OPERATOR,
            },
        )
        assert response.status_code == 400
        assert "already registered" in response.json()["detail"]

    def test_register_duplicate_email(self, client: TestClient, admin_user: User):
        response = client.post(
            "/auth/register",
            json={
                "username": "differentuser",
                "email": admin_user.email,
                "password": "password123",
                "role": UserRole.OPERATOR,
            },
        )
        assert response.status_code == 400
        assert "already registered" in response.json()["detail"]

    def test_register_missing_fields(self, client: TestClient):
        response = client.post(
            "/auth/register",
            json={"username": "incomplete"},
        )
        assert response.status_code == 422


class TestLogin:
    def test_login_success(self, client: TestClient, admin_user: User):
        response = client.post(
            "/auth/login",
            json={
                "username": "testadmin",
                "password": "admin123",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    def test_login_wrong_password(self, client: TestClient, admin_user: User):
        response = client.post(
            "/auth/login",
            json={
                "username": "testadmin",
                "password": "wrongpassword",
            },
        )
        assert response.status_code == 401
        assert "Incorrect" in response.json()["detail"]

    def test_login_nonexistent_user(self, client: TestClient, db: Session):
        response = client.post(
            "/auth/login",
            json={
                "username": "nonexistent",
                "password": "anypassword",
            },
        )
        assert response.status_code == 401
        assert "Incorrect" in response.json()["detail"]

    def test_login_inactive_user(self, client: TestClient, inactive_user: User):
        response = client.post(
            "/auth/login",
            json={
                "username": "inactiveuser",
                "password": "inactive123",
            },
        )
        assert response.status_code == 400
        assert "Inactive" in response.json()["detail"]

    def test_login_missing_fields(self, client: TestClient):
        response = client.post(
            "/auth/login",
            json={"username": "testuser"},
        )
        assert response.status_code == 422
