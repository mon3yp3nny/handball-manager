"""Tests for Teams CRUD endpoints."""
from tests.conftest import _make_user, _auth_header
from app.models.user import UserRole
from app.models.player import Player


class TestGetTeams:
    def test_admin_sees_all_teams(self, client, admin_headers, team):
        resp = client.get("/api/v1/teams/", headers=admin_headers)
        assert resp.status_code == 200
        names = [t["name"] for t in resp.json()]
        assert team.name in names

    def test_coach_sees_own_teams(self, client, coach_headers, team):
        resp = client.get("/api/v1/teams/", headers=coach_headers)
        assert resp.status_code == 200
        assert len(resp.json()) >= 1

    def test_unauthenticated(self, client):
        resp = client.get("/api/v1/teams/")
        assert resp.status_code == 401


class TestCreateTeam:
    def test_coach_creates_team(self, client, coach_user, coach_headers):
        resp = client.post(
            "/api/v1/teams/",
            headers=coach_headers,
            json={"name": "New Team", "age_group": "U14", "coach_id": coach_user.id},
        )
        assert resp.status_code == 201
        assert resp.json()["name"] == "New Team"

    def test_admin_creates_team(self, client, admin_headers):
        resp = client.post(
            "/api/v1/teams/",
            headers=admin_headers,
            json={"name": "Admin Team", "age_group": "U18"},
        )
        assert resp.status_code == 201

    def test_player_cannot_create_team(self, client, player_headers):
        resp = client.post(
            "/api/v1/teams/",
            headers=player_headers,
            json={"name": "Blocked Team"},
        )
        assert resp.status_code == 403


class TestGetTeam:
    def test_get_team_by_id(self, client, coach_headers, team):
        resp = client.get(f"/api/v1/teams/{team.id}", headers=coach_headers)
        assert resp.status_code == 200
        assert resp.json()["id"] == team.id

    def test_get_nonexistent_team(self, client, coach_headers):
        resp = client.get("/api/v1/teams/99999", headers=coach_headers)
        assert resp.status_code == 404


class TestUpdateTeam:
    def test_coach_updates_own_team(self, client, coach_headers, team):
        resp = client.put(
            f"/api/v1/teams/{team.id}",
            headers=coach_headers,
            json={"name": "Renamed Team"},
        )
        assert resp.status_code == 200
        assert resp.json()["name"] == "Renamed Team"

    def test_other_coach_cannot_update(self, client, db, team):
        other = _make_user(db, email="other_coach@test.com", role=UserRole.COACH)
        headers = _auth_header(other)
        resp = client.put(
            f"/api/v1/teams/{team.id}",
            headers=headers,
            json={"name": "Hijacked"},
        )
        assert resp.status_code == 403


class TestDeleteTeam:
    def test_coach_deletes_own_team(self, client, coach_headers, team):
        resp = client.delete(f"/api/v1/teams/{team.id}", headers=coach_headers)
        assert resp.status_code == 204

    def test_player_cannot_delete_team(self, client, player_headers, team):
        resp = client.delete(f"/api/v1/teams/{team.id}", headers=player_headers)
        assert resp.status_code == 403


class TestTeamPlayers:
    def test_add_player_to_team(self, client, coach_headers, team, db, player_user):
        p = Player(user_id=player_user.id)
        db.add(p)
        db.commit()
        db.refresh(p)
        resp = client.post(
            f"/api/v1/teams/{team.id}/players/{p.id}",
            headers=coach_headers,
        )
        assert resp.status_code == 200

    def test_remove_player_from_team(self, client, coach_headers, team, player_profile):
        resp = client.delete(
            f"/api/v1/teams/{team.id}/players/{player_profile.id}",
            headers=coach_headers,
        )
        assert resp.status_code == 200
