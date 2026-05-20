"""Tests for the dashboard widgets endpoint (#129)."""
from datetime import date, datetime, timedelta


class TestDashboardWidgets:
    def test_admin_sees_widgets_payload(self, client, admin_headers):
        r = client.get("/api/v1/dashboard/widgets", headers=admin_headers)
        assert r.status_code == 200
        body = r.json()
        assert "next_match" in body
        assert "upcoming_birthdays" in body
        assert isinstance(body["upcoming_birthdays"], list)

    def test_next_match_returns_nearest_upcoming(self, client, db, admin_headers, team):
        from app.models.game import Game, GameStatus

        # Two games — far first, near second; expect the nearer one back.
        far = Game(
            team_id=team.id,
            opponent="Far FC",
            location="Far",
            scheduled_at=datetime.utcnow() + timedelta(days=14),
            status=GameStatus.SCHEDULED,
        )
        near = Game(
            team_id=team.id,
            opponent="Near FC",
            location="Near",
            scheduled_at=datetime.utcnow() + timedelta(hours=4),
            status=GameStatus.SCHEDULED,
        )
        db.add_all([far, near])
        db.commit()

        r = client.get("/api/v1/dashboard/widgets", headers=admin_headers)
        assert r.json()["next_match"]["opponent"] == "Near FC"

    def test_upcoming_birthdays_includes_player_due_in_3_days(self, client, db, admin_headers, player_user, team):
        from app.models.player import Player

        target = date.today() + timedelta(days=3)
        # User fixture doesn't auto-create a Player row; do it here.
        player = Player(
            user_id=player_user.id,
            team_id=team.id,
            date_of_birth=target.replace(year=target.year - 12),
        )
        db.add(player)
        db.commit()

        r = client.get("/api/v1/dashboard/widgets", headers=admin_headers)
        days = [b["days_until"] for b in r.json()["upcoming_birthdays"]]
        assert 3 in days

    def test_player_only_sees_own_team_birthdays(self, client, db, player_user, player_headers, team):
        """A player on team A must not see team B players' birthdays."""
        from app.models.player import Player
        from app.models.team import Team
        from app.models.user import User, UserRole
        from app.core.security import get_password_hash

        # Add a different team with a player whose birthday is tomorrow.
        other_team = Team(name="Other")
        db.add(other_team); db.commit()
        other_user = User(
            email="other-bday@x.test",
            hashed_password=get_password_hash("x"),
            first_name="Other",
            last_name="Bday",
            role=UserRole.PLAYER,
        )
        db.add(other_user); db.commit()
        other_player = Player(
            user_id=other_user.id,
            team_id=other_team.id,
            date_of_birth=(date.today() + timedelta(days=1)).replace(year=2010),
        )
        db.add(other_player); db.commit()

        # `player_user` has no Player profile by default → no visible teams.
        r = client.get("/api/v1/dashboard/widgets", headers=player_headers)
        ids = [b["player_id"] for b in r.json()["upcoming_birthdays"]]
        assert other_player.id not in ids
