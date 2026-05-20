"""Tests for the player-availability endpoints (#136)."""
from datetime import date, timedelta


def _create_player_with_team(db, player_user, team):
    """Helper — make sure the seeded player_user has a Player row on `team`."""
    from app.models.player import Player

    p = db.query(Player).filter(Player.user_id == player_user.id).first()
    if not p:
        p = Player(user_id=player_user.id, team_id=team.id)
        db.add(p)
    else:
        p.team_id = team.id
    db.commit()
    return p


class TestAvailability:
    def test_admin_creates_and_lists(self, client, db, admin_headers, player_user, team):
        p = _create_player_with_team(db, player_user, team)
        body = {
            "from_date": str(date.today() + timedelta(days=1)),
            "to_date": str(date.today() + timedelta(days=7)),
            "reason": "holiday",
            "note": "Skiurlaub",
        }
        r = client.post(
            f"/api/v1/players/{p.id}/availability",
            headers=admin_headers,
            json=body,
        )
        assert r.status_code == 201
        assert r.json()["reason"] == "holiday"

        listed = client.get(
            f"/api/v1/players/{p.id}/availability", headers=admin_headers
        ).json()
        assert len(listed) == 1
        assert listed[0]["note"] == "Skiurlaub"

    def test_rejects_inverted_range(self, client, db, admin_headers, player_user, team):
        p = _create_player_with_team(db, player_user, team)
        r = client.post(
            f"/api/v1/players/{p.id}/availability",
            headers=admin_headers,
            json={
                "from_date": str(date.today() + timedelta(days=7)),
                "to_date": str(date.today() + timedelta(days=1)),
                "reason": "other",
            },
        )
        assert r.status_code in (400, 422)

    def test_player_cannot_self_flag_medical(self, client, db, player_user, player_headers, team):
        p = _create_player_with_team(db, player_user, team)
        r = client.post(
            f"/api/v1/players/{p.id}/availability",
            headers=player_headers,
            json={
                "from_date": str(date.today()),
                "to_date": str(date.today() + timedelta(days=3)),
                "reason": "injury",
                "note": "Knöchel",
                "is_medical": True,
            },
        )
        assert r.status_code == 403

    def test_coach_can_flag_medical_and_player_sees_note_redacted(
        self, client, db, coach_headers, player_user, player_headers, team
    ):
        # Coach owns the team via the fixture, player is on it.
        p = _create_player_with_team(db, player_user, team)
        r = client.post(
            f"/api/v1/players/{p.id}/availability",
            headers=coach_headers,
            json={
                "from_date": str(date.today()),
                "to_date": str(date.today() + timedelta(days=10)),
                "reason": "injury",
                "note": "Bänderriss",
                "is_medical": True,
            },
        )
        assert r.status_code == 201

        # Coach reads the note.
        coach_view = client.get(
            f"/api/v1/players/{p.id}/availability", headers=coach_headers
        ).json()[0]
        assert coach_view["note"] == "Bänderriss"

        # Player sees the row but the medical note is redacted.
        player_view = client.get(
            f"/api/v1/players/{p.id}/availability", headers=player_headers
        ).json()[0]
        assert player_view["is_medical"] is True
        assert player_view["note"] is None

    def test_outsider_player_cannot_access(self, client, db, player_user, team):
        """A different player (no team) tries to read team-mate availability."""
        from app.models.user import User, UserRole
        from app.models.player import Player
        from app.core.security import get_password_hash, create_access_token

        # Target player on `team`.
        target = _create_player_with_team(db, player_user, team)

        # Outsider user — no Player row at all, so no team access.
        outsider = User(
            email="outsider@x.test",
            hashed_password=get_password_hash("x"),
            first_name="O",
            last_name="S",
            role=UserRole.PLAYER,
        )
        db.add(outsider)
        db.commit()
        token = create_access_token({"sub": outsider.email})
        hdr = {"Authorization": f"Bearer {token}"}

        r = client.get(f"/api/v1/players/{target.id}/availability", headers=hdr)
        assert r.status_code == 403

    def test_upcoming_only_filter(self, client, db, admin_headers, player_user, team):
        p = _create_player_with_team(db, player_user, team)
        # Past window
        client.post(
            f"/api/v1/players/{p.id}/availability",
            headers=admin_headers,
            json={
                "from_date": str(date.today() - timedelta(days=30)),
                "to_date": str(date.today() - timedelta(days=20)),
                "reason": "holiday",
            },
        )
        # Future window
        client.post(
            f"/api/v1/players/{p.id}/availability",
            headers=admin_headers,
            json={
                "from_date": str(date.today() + timedelta(days=5)),
                "to_date": str(date.today() + timedelta(days=10)),
                "reason": "holiday",
            },
        )

        all_rows = client.get(
            f"/api/v1/players/{p.id}/availability", headers=admin_headers
        ).json()
        upcoming = client.get(
            f"/api/v1/players/{p.id}/availability?upcoming_only=true",
            headers=admin_headers,
        ).json()
        assert len(all_rows) == 2
        assert len(upcoming) == 1
