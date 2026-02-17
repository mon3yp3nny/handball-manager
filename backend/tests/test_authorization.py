"""Tests that verify role-based access control across endpoints."""
from tests.conftest import _make_user, _auth_header
from app.models.user import UserRole


class TestAdminAccess:
    """Admin should have full access everywhere."""

    def test_admin_lists_users(self, client, admin_headers, admin_user):
        assert client.get("/api/v1/users/", headers=admin_headers).status_code == 200

    def test_admin_creates_user(self, client, admin_headers):
        resp = client.post(
            "/api/v1/users/",
            headers=admin_headers,
            json={
                "email": "auth_test@test.com",
                "password": "securepass123",
                "first_name": "A",
                "last_name": "B",
                "role": "player",
            },
        )
        assert resp.status_code == 201

    def test_admin_deletes_user(self, client, admin_headers, db):
        u = _make_user(db, email="todel@test.com", role=UserRole.PLAYER)
        assert client.delete(f"/api/v1/users/{u.id}", headers=admin_headers).status_code == 204


class TestCoachAccess:
    """Coach should be able to manage teams and content but not admin-only actions."""

    def test_coach_can_list_users(self, client, coach_headers):
        assert client.get("/api/v1/users/", headers=coach_headers).status_code == 200

    def test_coach_cannot_delete_users(self, client, coach_headers, db):
        u = _make_user(db, email="nodelete2@test.com", role=UserRole.PLAYER)
        assert client.delete(f"/api/v1/users/{u.id}", headers=coach_headers).status_code == 403

    def test_coach_can_create_team(self, client, coach_headers):
        resp = client.post(
            "/api/v1/teams/",
            headers=coach_headers,
            json={"name": "Auth Team"},
        )
        assert resp.status_code == 201


class TestPlayerAccess:
    """Player should have read-mostly access with no admin/coach capabilities."""

    def test_player_cannot_list_users(self, client, player_headers):
        assert client.get("/api/v1/users/", headers=player_headers).status_code == 403

    def test_player_cannot_create_team(self, client, player_headers):
        resp = client.post(
            "/api/v1/teams/",
            headers=player_headers,
            json={"name": "Nope"},
        )
        assert resp.status_code == 403

    def test_player_cannot_create_news(self, client, player_headers):
        resp = client.post(
            "/api/v1/news/",
            headers=player_headers,
            json={"title": "X", "content": "Y"},
        )
        assert resp.status_code == 403


class TestParentAccess:
    """Parent should only access child-related data."""

    def test_parent_cannot_list_users(self, client, parent_headers):
        assert client.get("/api/v1/users/", headers=parent_headers).status_code == 403

    def test_parent_cannot_create_team(self, client, parent_headers):
        resp = client.post(
            "/api/v1/teams/",
            headers=parent_headers,
            json={"name": "Nope"},
        )
        assert resp.status_code == 403

    def test_parent_cannot_create_game(self, client, parent_headers, team):
        from datetime import datetime, timedelta

        future = (datetime.utcnow() + timedelta(days=7)).isoformat()
        resp = client.post(
            "/api/v1/games/",
            headers=parent_headers,
            json={"team_id": team.id, "opponent": "X", "location": "Y", "scheduled_at": future},
        )
        assert resp.status_code == 403


class TestSupervisorAccess:
    """Supervisor should be able to manage games/news but not admin things."""

    def test_supervisor_can_create_news(self, client, supervisor_headers, team):
        resp = client.post(
            "/api/v1/news/",
            headers=supervisor_headers,
            json={"title": "Sup News", "content": "Info", "team_id": team.id},
        )
        assert resp.status_code == 201

    def test_supervisor_cannot_list_users(self, client, supervisor_headers):
        assert client.get("/api/v1/users/", headers=supervisor_headers).status_code == 403

    def test_supervisor_cannot_create_team(self, client, supervisor_headers):
        resp = client.post(
            "/api/v1/teams/",
            headers=supervisor_headers,
            json={"name": "Nope"},
        )
        assert resp.status_code == 403
