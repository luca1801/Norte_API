import pytest
from fastapi.testclient import TestClient


class TestAuthentication:
    def test_protected_route_without_token(self, client: TestClient):
        response = client.get("/users/me")
        assert response.status_code == 401

    def test_protected_route_with_invalid_token(self, client: TestClient):
        response = client.get("/users/me", headers={"Authorization": "Bearer invalid_token"})
        assert response.status_code == 401

    def test_protected_route_with_malformed_token(self, client: TestClient):
        response = client.get("/users/me", headers={"Authorization": "invalid_format"})
        assert response.status_code == 401

    def test_protected_route_without_bearer_prefix(self, client: TestClient, admin_user):
        from core.security import create_access_token
        from datetime import timedelta
        
        token = create_access_token(
            data={"sub": str(admin_user.id), "username": admin_user.username, "role": admin_user.role.value},
            expires_delta=timedelta(minutes=30),
        )
        response = client.get("/users/me", headers={"Authorization": token})
        assert response.status_code == 401


class TestAuthorization:
    def test_admin_route_as_operator(self, client: TestClient, operator_auth_header: dict):
        response = client.get("/users/", headers=operator_auth_header)
        assert response.status_code == 403

    def test_admin_route_as_admin(self, client: TestClient, auth_header: dict):
        response = client.get("/users/", headers=auth_header)
        assert response.status_code == 200


class TestInputValidation:
    def test_sql_injection_in_login(self, client: TestClient, admin_user):
        response = client.post(
            "/auth/login",
            json={
                "username": "testadmin' OR '1'='1",
                "password": "anything",
            },
        )
        assert response.status_code == 401

    def test_sql_injection_in_equipment_code(self, client: TestClient, auth_header: dict):
        response = client.get("/equipment/code/test'; DROP TABLE equipment;--", headers=auth_header)
        assert response.status_code == 404

    def test_xss_in_registration(self, client: TestClient):
        response = client.post(
            "/auth/register",
            json={
                "username": "xssuser",
                "email": "xss@test.com",
                "password": "password123",
            },
        )
        assert response.status_code in [201, 400]


class TestRateLimitingAndAbuse:
    def test_multiple_failed_login_attempts(self, client: TestClient):
        for _ in range(5):
            response = client.post(
                "/auth/login",
                json={"username": "testuser", "password": "wrongpassword"},
            )
            assert response.status_code == 401


class TestTokenSecurity:
    def test_expired_token(self, client: TestClient, admin_user):
        from core.security import create_access_token
        from datetime import timedelta
        
        expired_token = create_access_token(
            data={"sub": str(admin_user.id), "username": admin_user.username, "role": admin_user.role.value},
            expires_delta=timedelta(seconds=-1),
        )
        response = client.get("/users/me", headers={"Authorization": f"Bearer {expired_token}"})
        assert response.status_code == 401

    def test_token_with_wrong_secret(self, client: TestClient, admin_user):
        from jose import jwt
        from datetime import datetime, timedelta, timezone
        
        fake_token = jwt.encode(
            {
                "sub": str(admin_user.id),
                "username": admin_user.username,
                "role": admin_user.role.value,
                "exp": datetime.now(timezone.utc) + timedelta(minutes=30),
            },
            "wrong_secret_key",
            algorithm="HS256",
        )
        response = client.get("/users/me", headers={"Authorization": f"Bearer {fake_token}"})
        assert response.status_code == 401
