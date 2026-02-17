"""Tests for Players CRUD endpoints."""
from tests.conftest import _make_user, _auth_header
from app.models.user import UserRole
from app.models.player import Player


class TestGetPlayers:
    def test_admin_lists_all_players(self, client, admin_headers, player_profile):
        resp = client.get("/api/v1/players/", headers=admin_headers)
        assert resp.status_code == 200
        assert len(resp.json()) >= 1

    def test_coach_lists_team_players(self, client, coach_headers, player_profile):
        resp = client.get("/api/v1/players/", headers=coach_headers)
        assert resp.status_code == 200

    def test_unauthenticated(self, client):
        resp = client.get("/api/v1/players/")
        assert resp.status_code == 401


class TestCreatePlayer:
    def test_coach_creates_player(self, client, coach_headers, db):
        user = _make_user(db, email="newplayer@test.com", role=UserRole.PLAYER)
        resp = client.post(
            "/api/v1/players/",
            headers=coach_headers,
            json={"user_id": user.id, "jersey_number": 10, "position": "goalkeeper"},
        )
        assert resp.status_code == 201
        assert resp.json()["jersey_number"] == 10

    def test_player_cannot_create_player(self, client, player_headers, db):
        user = _make_user(db, email="nope@test.com", role=UserRole.PLAYER)
        resp = client.post(
            "/api/v1/players/",
            headers=player_headers,
            json={"user_id": user.id},
        )
        assert resp.status_code == 403

    def test_create_duplicate_player(self, client, coach_headers, player_user, player_profile):
        resp = client.post(
            "/api/v1/players/",
            headers=coach_headers,
            json={"user_id": player_user.id},
        )
        assert resp.status_code == 400
        assert "already exists" in resp.json()["detail"]


class TestGetPlayer:
    def test_get_player_by_id(self, client, coach_headers, player_profile):
        resp = client.get(f"/api/v1/players/{player_profile.id}", headers=coach_headers)
        assert resp.status_code == 200
        assert resp.json()["id"] == player_profile.id

    def test_get_nonexistent_player(self, client, coach_headers):
        resp = client.get("/api/v1/players/99999", headers=coach_headers)
        assert resp.status_code == 404


class TestUpdatePlayer:
    def test_coach_updates_player(self, client, coach_headers, player_profile):
        resp = client.put(
            f"/api/v1/players/{player_profile.id}",
            headers=coach_headers,
            json={"jersey_number": 99},
        )
        assert resp.status_code == 200
        assert resp.json()["jersey_number"] == 99

    def test_player_updates_own_profile(self, client, player_headers, player_profile):
        resp = client.put(
            f"/api/v1/players/{player_profile.id}",
            headers=player_headers,
            json={"emergency_contact_name": "Mom"},
        )
        assert resp.status_code == 200
        assert resp.json()["emergency_contact_name"] == "Mom"


class TestDeletePlayer:
    def test_admin_deletes_player(self, client, admin_headers, player_profile):
        resp = client.delete(f"/api/v1/players/{player_profile.id}", headers=admin_headers)
        assert resp.status_code == 204

    def test_coach_cannot_delete_player(self, client, coach_headers, player_profile):
        resp = client.delete(f"/api/v1/players/{player_profile.id}", headers=coach_headers)
        assert resp.status_code == 403

    def test_delete_nonexistent(self, client, admin_headers):
        resp = client.delete("/api/v1/players/99999", headers=admin_headers)
        assert resp.status_code == 404
