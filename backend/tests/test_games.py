"""Tests for Games CRUD endpoints."""
from datetime import datetime, timedelta
from tests.conftest import _make_user, _auth_header
from app.models.user import UserRole


class TestGetGames:
    def test_admin_lists_games(self, client, admin_headers, game):
        resp = client.get("/api/v1/games/", headers=admin_headers)
        assert resp.status_code == 200
        assert len(resp.json()) >= 1

    def test_filter_by_team(self, client, coach_headers, game, team):
        resp = client.get(f"/api/v1/games/?team_id={team.id}", headers=coach_headers)
        assert resp.status_code == 200
        for g in resp.json():
            assert g["team_id"] == team.id

    def test_unauthenticated(self, client):
        resp = client.get("/api/v1/games/")
        assert resp.status_code == 401


class TestCreateGame:
    def test_coach_creates_game(self, client, coach_headers, team):
        future = (datetime.utcnow() + timedelta(days=7)).isoformat()
        resp = client.post(
            "/api/v1/games/",
            headers=coach_headers,
            json={
                "team_id": team.id,
                "opponent": "New Rival",
                "location": "Away Arena",
                "scheduled_at": future,
                "game_type": "friendly",
                "is_home_game": False,
            },
        )
        assert resp.status_code == 201
        assert resp.json()["opponent"] == "New Rival"

    def test_player_cannot_create_game(self, client, player_headers, team):
        future = (datetime.utcnow() + timedelta(days=7)).isoformat()
        resp = client.post(
            "/api/v1/games/",
            headers=player_headers,
            json={
                "team_id": team.id,
                "opponent": "X",
                "location": "Y",
                "scheduled_at": future,
            },
        )
        assert resp.status_code == 403

    def test_create_game_nonexistent_team(self, client, coach_headers):
        future = (datetime.utcnow() + timedelta(days=7)).isoformat()
        resp = client.post(
            "/api/v1/games/",
            headers=coach_headers,
            json={
                "team_id": 99999,
                "opponent": "X",
                "location": "Y",
                "scheduled_at": future,
            },
        )
        assert resp.status_code == 404


class TestGetGame:
    def test_get_game_by_id(self, client, coach_headers, game):
        resp = client.get(f"/api/v1/games/{game.id}", headers=coach_headers)
        assert resp.status_code == 200
        assert resp.json()["id"] == game.id

    def test_get_nonexistent_game(self, client, coach_headers):
        resp = client.get("/api/v1/games/99999", headers=coach_headers)
        assert resp.status_code == 404


class TestUpdateGame:
    def test_coach_updates_game(self, client, coach_headers, game):
        resp = client.put(
            f"/api/v1/games/{game.id}",
            headers=coach_headers,
            json={"opponent": "Updated Rival"},
        )
        assert resp.status_code == 200
        assert resp.json()["opponent"] == "Updated Rival"


class TestGameResult:
    def test_coach_sets_result(self, client, coach_headers, game):
        resp = client.patch(
            f"/api/v1/games/{game.id}/result",
            headers=coach_headers,
            json={"home_score": 25, "away_score": 20, "status": "completed"},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["home_score"] == 25
        assert body["away_score"] == 20
        assert body["status"] == "completed"

    def test_supervisor_can_set_result(self, client, supervisor_headers, game):
        resp = client.patch(
            f"/api/v1/games/{game.id}/result",
            headers=supervisor_headers,
            json={"home_score": 30, "away_score": 28},
        )
        assert resp.status_code == 200

    def test_player_cannot_set_result(self, client, player_headers, game):
        resp = client.patch(
            f"/api/v1/games/{game.id}/result",
            headers=player_headers,
            json={"home_score": 10, "away_score": 5},
        )
        assert resp.status_code == 403


class TestDeleteGame:
    def test_coach_deletes_game(self, client, coach_headers, game):
        resp = client.delete(f"/api/v1/games/{game.id}", headers=coach_headers)
        assert resp.status_code == 204

    def test_player_cannot_delete_game(self, client, player_headers, game):
        resp = client.delete(f"/api/v1/games/{game.id}", headers=player_headers)
        assert resp.status_code == 403
