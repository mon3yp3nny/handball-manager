"""Tests for Events CRUD endpoints."""
from datetime import datetime, timedelta
from tests.conftest import _make_user, _auth_header
from app.models.user import UserRole


class TestGetEvents:
    def test_admin_lists_events(self, client, admin_headers, event_obj):
        resp = client.get("/api/v1/events/", headers=admin_headers)
        assert resp.status_code == 200
        assert len(resp.json()) >= 1

    def test_coach_sees_events(self, client, coach_headers, event_obj):
        resp = client.get("/api/v1/events/", headers=coach_headers)
        assert resp.status_code == 200

    def test_unauthenticated(self, client):
        resp = client.get("/api/v1/events/")
        assert resp.status_code == 401


class TestCreateEvent:
    def test_coach_creates_event(self, client, coach_headers, team):
        start = (datetime.utcnow() + timedelta(days=2)).isoformat()
        end = (datetime.utcnow() + timedelta(days=2, hours=2)).isoformat()
        resp = client.post(
            "/api/v1/events/",
            headers=coach_headers,
            json={
                "title": "Practice",
                "team_id": team.id,
                "event_type": "training",
                "location": "Gym",
                "start_time": start,
                "end_time": end,
            },
        )
        assert resp.status_code == 201
        assert resp.json()["title"] == "Practice"

    def test_player_cannot_create_event(self, client, player_headers, team):
        start = (datetime.utcnow() + timedelta(days=2)).isoformat()
        end = (datetime.utcnow() + timedelta(days=2, hours=2)).isoformat()
        resp = client.post(
            "/api/v1/events/",
            headers=player_headers,
            json={
                "title": "Bad",
                "team_id": team.id,
                "start_time": start,
                "end_time": end,
            },
        )
        assert resp.status_code == 403

    def test_end_before_start_rejected(self, client, coach_headers, team):
        start = (datetime.utcnow() + timedelta(days=2, hours=2)).isoformat()
        end = (datetime.utcnow() + timedelta(days=2)).isoformat()
        resp = client.post(
            "/api/v1/events/",
            headers=coach_headers,
            json={
                "title": "Invalid",
                "team_id": team.id,
                "start_time": start,
                "end_time": end,
            },
        )
        assert resp.status_code == 400
        assert "End time must be after start time" in resp.json()["detail"]


class TestGetEvent:
    def test_get_event_by_id(self, client, coach_headers, event_obj):
        resp = client.get(f"/api/v1/events/{event_obj.id}", headers=coach_headers)
        assert resp.status_code == 200
        assert resp.json()["id"] == event_obj.id

    def test_get_nonexistent_event(self, client, coach_headers):
        resp = client.get("/api/v1/events/99999", headers=coach_headers)
        assert resp.status_code == 404


class TestUpdateEvent:
    def test_coach_updates_event(self, client, coach_headers, event_obj):
        resp = client.put(
            f"/api/v1/events/{event_obj.id}",
            headers=coach_headers,
            json={"title": "Updated Practice"},
        )
        assert resp.status_code == 200
        assert resp.json()["title"] == "Updated Practice"


class TestDeleteEvent:
    def test_coach_deletes_event(self, client, coach_headers, event_obj):
        resp = client.delete(f"/api/v1/events/{event_obj.id}", headers=coach_headers)
        assert resp.status_code == 204

    def test_player_cannot_delete_event(self, client, player_headers, event_obj):
        resp = client.delete(f"/api/v1/events/{event_obj.id}", headers=player_headers)
        assert resp.status_code == 403
