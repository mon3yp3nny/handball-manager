"""Tests for Attendance endpoints."""
from tests.conftest import _make_user, _auth_header
from app.models.user import UserRole


class TestGetAttendance:
    def test_coach_lists_attendance(self, client, coach_headers, attendance_record):
        resp = client.get("/api/v1/attendance/", headers=coach_headers)
        assert resp.status_code == 200

    def test_unauthenticated(self, client):
        resp = client.get("/api/v1/attendance/")
        assert resp.status_code == 401


class TestCreateAttendance:
    def test_coach_creates_attendance(self, client, coach_headers, player_profile, game):
        resp = client.post(
            "/api/v1/attendance/",
            headers=coach_headers,
            json={
                "player_id": player_profile.id,
                "game_id": game.id,
                "status": "present",
            },
        )
        assert resp.status_code == 201
        assert resp.json()["status"] == "present"

    def test_missing_game_and_event(self, client, coach_headers, player_profile):
        resp = client.post(
            "/api/v1/attendance/",
            headers=coach_headers,
            json={"player_id": player_profile.id, "status": "present"},
        )
        assert resp.status_code == 400
        assert "game_id or event_id" in resp.json()["detail"]

    def test_duplicate_attendance(self, client, coach_headers, attendance_record, player_profile, game):
        resp = client.post(
            "/api/v1/attendance/",
            headers=coach_headers,
            json={
                "player_id": player_profile.id,
                "game_id": game.id,
                "status": "present",
            },
        )
        assert resp.status_code == 400
        assert "already exists" in resp.json()["detail"]


class TestGetAttendanceRecord:
    def test_get_by_id(self, client, coach_headers, attendance_record):
        resp = client.get(
            f"/api/v1/attendance/{attendance_record.id}", headers=coach_headers
        )
        assert resp.status_code == 200
        assert resp.json()["id"] == attendance_record.id

    def test_get_nonexistent(self, client, coach_headers):
        resp = client.get("/api/v1/attendance/99999", headers=coach_headers)
        assert resp.status_code == 404


class TestUpdateAttendance:
    def test_coach_updates_attendance(self, client, coach_headers, attendance_record):
        resp = client.put(
            f"/api/v1/attendance/{attendance_record.id}",
            headers=coach_headers,
            json={"status": "present"},
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "present"


class TestBulkAttendance:
    def test_coach_bulk_updates(self, client, coach_headers, player_profile, game):
        resp = client.post(
            f"/api/v1/attendance/bulk-update?game_id={game.id}",
            headers=coach_headers,
            json={
                "player_ids": [player_profile.id],
                "status": "present",
            },
        )
        assert resp.status_code == 200
        assert len(resp.json()) == 1

    def test_player_cannot_bulk_update(self, client, player_headers, player_profile, game):
        resp = client.post(
            f"/api/v1/attendance/bulk-update?game_id={game.id}",
            headers=player_headers,
            json={
                "player_ids": [player_profile.id],
                "status": "present",
            },
        )
        assert resp.status_code == 403


class TestAttendanceStats:
    def test_get_player_stats(self, client, coach_headers, attendance_record, player_profile):
        resp = client.get(
            f"/api/v1/attendance/stats/player/{player_profile.id}",
            headers=coach_headers,
        )
        assert resp.status_code == 200
        body = resp.json()
        assert "total" in body
        assert "attendance_rate" in body

    def test_empty_stats(self, client, coach_headers, db, team):
        from app.models.player import Player

        user = _make_user(db, email="nostats@test.com", role=UserRole.PLAYER)
        p = Player(user_id=user.id, team_id=team.id)
        db.add(p)
        db.commit()
        db.refresh(p)
        resp = client.get(
            f"/api/v1/attendance/stats/player/{p.id}",
            headers=coach_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["total"] == 0
