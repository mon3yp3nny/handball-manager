"""Tests for the iCalendar subscription feed."""
from datetime import datetime, timedelta, timezone


class TestCalendarToken:
    def test_get_token_creates_lazily(self, client, coach_headers):
        # First call generates a token.
        r1 = client.get("/api/v1/calendar/me/token", headers=coach_headers)
        assert r1.status_code == 200
        body1 = r1.json()
        assert body1["token"]
        assert "/api/v1/calendar/" in body1["url"]
        assert body1["url"].endswith(".ics")

        # Second call returns the same token (idempotent read).
        r2 = client.get("/api/v1/calendar/me/token", headers=coach_headers)
        assert r2.json()["token"] == body1["token"]

    def test_rotate_invalidates_old_token(self, client, coach_headers):
        old = client.get("/api/v1/calendar/me/token", headers=coach_headers).json()["token"]
        rot = client.post("/api/v1/calendar/me/token", headers=coach_headers)
        assert rot.status_code == 200
        assert rot.json()["token"] != old

        # Old token no longer resolves.
        bad = client.get(f"/api/v1/calendar/{old}.ics")
        assert bad.status_code == 404

    def test_token_required_to_read_feed(self, client):
        r = client.get("/api/v1/calendar/not-a-real-token.ics")
        assert r.status_code == 404


class TestCalendarFeed:
    def test_feed_returns_text_calendar(self, client, coach_headers):
        token = client.get("/api/v1/calendar/me/token", headers=coach_headers).json()["token"]
        r = client.get(f"/api/v1/calendar/{token}.ics")
        assert r.status_code == 200
        assert r.headers["content-type"].startswith("text/calendar")
        body = r.text
        assert body.startswith("BEGIN:VCALENDAR\r\n")
        assert "VERSION:2.0" in body
        assert body.rstrip().endswith("END:VCALENDAR")

    def test_feed_includes_visible_events(self, client, db, coach_user, coach_headers, team):
        from app.models.event import Event, EventType, EventVisibility

        start = datetime.now(timezone.utc) + timedelta(days=3)
        ev = Event(
            title="Wichtiges Training",
            description="Pflicht-Termin",
            team_id=team.id,
            event_type=EventType.TRAINING,
            visibility=EventVisibility.TEAM,
            location="Halle A",
            start_time=start.replace(tzinfo=None),
            end_time=(start + timedelta(hours=1)).replace(tzinfo=None),
        )
        db.add(ev)
        db.commit()

        token = client.get("/api/v1/calendar/me/token", headers=coach_headers).json()["token"]
        body = client.get(f"/api/v1/calendar/{token}.ics").text
        assert "BEGIN:VEVENT" in body
        assert "Wichtiges Training" in body
        assert "Halle A" in body
        # Coach owns the team — they should see this team's event.

    def test_feed_hides_other_teams_events_from_player(self, client, db, player_user, player_headers, team):
        """A player only on team A should not see team B's events."""
        from app.models.event import Event, EventType, EventVisibility
        from app.models.team import Team
        from app.models.user import User, UserRole
        from app.core.security import get_password_hash

        # Player_user is not on this team in the default fixture, so any
        # event we add here is on a team the player can't see.
        other_team = Team(name="Other Team")
        db.add(other_team)
        db.commit()

        start = datetime.now(timezone.utc) + timedelta(days=1)
        ev = Event(
            title="GeheimesEvent",
            team_id=other_team.id,
            event_type=EventType.TRAINING,
            visibility=EventVisibility.TEAM,
            start_time=start.replace(tzinfo=None),
            end_time=(start + timedelta(hours=1)).replace(tzinfo=None),
        )
        db.add(ev)
        db.commit()

        token = client.get("/api/v1/calendar/me/token", headers=player_headers).json()["token"]
        body = client.get(f"/api/v1/calendar/{token}.ics").text
        assert "GeheimesEvent" not in body
