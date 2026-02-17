"""Tests for authentication endpoints: login, token refresh, /me."""
from tests.conftest import _make_user, _make_token, _auth_header
from app.models.user import UserRole
from app.core.security import create_refresh_token


class TestLogin:
    def test_login_success(self, client, db):
        user = _make_user(db, email="login@test.com", role=UserRole.COACH)
        resp = client.post(
            "/api/v1/auth/login",
            data={"username": "login@test.com", "password": "testpassword123"},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert "access_token" in body
        assert "refresh_token" in body
        assert body["token_type"] == "bearer"

    def test_login_wrong_password(self, client, db):
        _make_user(db, email="bad@test.com", role=UserRole.COACH)
        resp = client.post(
            "/api/v1/auth/login",
            data={"username": "bad@test.com", "password": "wrongpassword1"},
        )
        assert resp.status_code == 401
        assert "Incorrect email or password" in resp.json()["detail"]

    def test_login_nonexistent_user(self, client):
        resp = client.post(
            "/api/v1/auth/login",
            data={"username": "nobody@test.com", "password": "testpassword123"},
        )
        assert resp.status_code == 401

    def test_login_inactive_user(self, client, db):
        user = _make_user(db, email="inactive@test.com", role=UserRole.PLAYER)
        user.is_active = False
        db.commit()
        resp = client.post(
            "/api/v1/auth/login",
            data={"username": "inactive@test.com", "password": "testpassword123"},
        )
        assert resp.status_code == 401


class TestRefreshToken:
    def test_refresh_success(self, client, db):
        user = _make_user(db, email="refresh@test.com", role=UserRole.COACH)
        refresh = create_refresh_token(data={"sub": user.email})
        resp = client.post(
            "/api/v1/auth/refresh",
            params={"refresh_token": refresh},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert "access_token" in body
        assert "refresh_token" in body

    def test_refresh_with_access_token_fails(self, client, db):
        user = _make_user(db, email="wrongtype@test.com", role=UserRole.COACH)
        access = _make_token(user)
        resp = client.post(
            "/api/v1/auth/refresh",
            params={"refresh_token": access},
        )
        assert resp.status_code == 401

    def test_refresh_with_garbage_token(self, client):
        resp = client.post(
            "/api/v1/auth/refresh",
            params={"refresh_token": "not-a-real-token"},
        )
        assert resp.status_code == 401


class TestMe:
    def test_me_returns_current_user(self, client, coach_user, coach_headers):
        resp = client.get("/api/v1/auth/me", headers=coach_headers)
        assert resp.status_code == 200
        body = resp.json()
        assert body["email"] == coach_user.email
        assert body["role"] == "coach"

    def test_me_unauthenticated(self, client):
        resp = client.get("/api/v1/auth/me")
        assert resp.status_code == 401

    def test_me_with_invalid_token(self, client):
        resp = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "Bearer invalid-garbage-token"},
        )
        assert resp.status_code == 401
