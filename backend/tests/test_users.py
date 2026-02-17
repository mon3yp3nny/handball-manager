"""Tests for Users CRUD endpoints."""
from tests.conftest import _make_user, _auth_header
from app.models.user import UserRole


class TestGetUsers:
    def test_admin_can_list_users(self, client, admin_headers, admin_user):
        resp = client.get("/api/v1/users/", headers=admin_headers)
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_coach_can_list_users(self, client, coach_headers):
        resp = client.get("/api/v1/users/", headers=coach_headers)
        assert resp.status_code == 200

    def test_player_cannot_list_users(self, client, player_headers):
        resp = client.get("/api/v1/users/", headers=player_headers)
        assert resp.status_code == 403

    def test_parent_cannot_list_users(self, client, parent_headers):
        resp = client.get("/api/v1/users/", headers=parent_headers)
        assert resp.status_code == 403

    def test_filter_by_role(self, client, admin_headers, db):
        _make_user(db, email="another_coach@test.com", role=UserRole.COACH)
        resp = client.get("/api/v1/users/?role=coach", headers=admin_headers)
        assert resp.status_code == 200
        for u in resp.json():
            assert u["role"] == "coach"

    def test_unauthenticated(self, client):
        resp = client.get("/api/v1/users/")
        assert resp.status_code == 401


class TestCreateUser:
    def test_admin_creates_user(self, client, admin_headers):
        resp = client.post(
            "/api/v1/users/",
            headers=admin_headers,
            json={
                "email": "new@test.com",
                "password": "securepass123",
                "first_name": "New",
                "last_name": "User",
                "role": "player",
            },
        )
        assert resp.status_code == 201
        body = resp.json()
        assert body["email"] == "new@test.com"
        assert body["role"] == "player"

    def test_coach_cannot_create_user(self, client, coach_headers):
        resp = client.post(
            "/api/v1/users/",
            headers=coach_headers,
            json={
                "email": "blocked@test.com",
                "password": "securepass123",
                "first_name": "Blocked",
                "last_name": "User",
                "role": "player",
            },
        )
        assert resp.status_code == 403

    def test_duplicate_email(self, client, admin_headers, admin_user):
        resp = client.post(
            "/api/v1/users/",
            headers=admin_headers,
            json={
                "email": admin_user.email,
                "password": "securepass123",
                "first_name": "Dup",
                "last_name": "User",
                "role": "player",
            },
        )
        assert resp.status_code == 400
        assert "already registered" in resp.json()["detail"]


class TestGetUser:
    def test_get_user_by_id(self, client, admin_headers, admin_user):
        resp = client.get(f"/api/v1/users/{admin_user.id}", headers=admin_headers)
        assert resp.status_code == 200
        assert resp.json()["id"] == admin_user.id

    def test_get_nonexistent_user(self, client, admin_headers):
        resp = client.get("/api/v1/users/99999", headers=admin_headers)
        assert resp.status_code == 404


class TestUpdateUser:
    def test_admin_updates_user(self, client, admin_headers, db):
        user = _make_user(db, email="target@test.com", role=UserRole.PLAYER)
        resp = client.put(
            f"/api/v1/users/{user.id}",
            headers=admin_headers,
            json={"first_name": "Updated"},
        )
        assert resp.status_code == 200
        assert resp.json()["first_name"] == "Updated"

    def test_user_can_update_self(self, client, player_user, player_headers):
        resp = client.put(
            f"/api/v1/users/{player_user.id}",
            headers=player_headers,
            json={"first_name": "NewName"},
        )
        assert resp.status_code == 200
        assert resp.json()["first_name"] == "NewName"

    def test_player_cannot_update_other(self, client, player_headers, db):
        other = _make_user(db, email="other@test.com", role=UserRole.PLAYER)
        resp = client.put(
            f"/api/v1/users/{other.id}",
            headers=player_headers,
            json={"first_name": "Hacked"},
        )
        assert resp.status_code == 403

    def test_non_admin_cannot_change_role(self, client, coach_user, coach_headers):
        resp = client.put(
            f"/api/v1/users/{coach_user.id}",
            headers=coach_headers,
            json={"role": "admin"},
        )
        assert resp.status_code == 403


class TestDeleteUser:
    def test_admin_deletes_user(self, client, admin_headers, db):
        user = _make_user(db, email="del@test.com", role=UserRole.PLAYER)
        resp = client.delete(f"/api/v1/users/{user.id}", headers=admin_headers)
        assert resp.status_code == 204

    def test_coach_cannot_delete_user(self, client, coach_headers, db):
        user = _make_user(db, email="nodelete@test.com", role=UserRole.PLAYER)
        resp = client.delete(f"/api/v1/users/{user.id}", headers=coach_headers)
        assert resp.status_code == 403

    def test_delete_nonexistent(self, client, admin_headers):
        resp = client.delete("/api/v1/users/99999", headers=admin_headers)
        assert resp.status_code == 404
