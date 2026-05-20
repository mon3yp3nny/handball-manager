"""Tests for team standings computed from completed games (#128)."""
from datetime import datetime, timedelta


def _completed_game(team, opponent, home_score, away_score, is_home_game, days_ago=1):
    from app.models.game import Game, GameStatus
    return Game(
        team_id=team.id,
        opponent=opponent,
        location="Halle",
        scheduled_at=datetime.utcnow() - timedelta(days=days_ago),
        status=GameStatus.COMPLETED,
        home_score=home_score,
        away_score=away_score,
        is_home_game=is_home_game,
    )


class TestStandings:
    def test_team_with_no_completed_games_returns_zeros(self, client, admin_headers, team):
        r = client.get(f"/api/v1/teams/{team.id}/standings", headers=admin_headers)
        assert r.status_code == 200
        body = r.json()
        assert body["team_id"] == team.id
        assert body["summary"]["played"] == 0
        assert body["summary"]["points"] == 0
        assert body["per_opponent"] == []

    def test_aggregates_one_win_one_draw_one_loss(self, client, db, admin_headers, team):
        # vs A: home, won 28:25 → win, gf 28 ga 25
        # vs B: away, drew 22:22 → draw, gf 22 ga 22
        # vs C: home, lost 18:24 → loss, gf 18 ga 24
        db.add_all([
            _completed_game(team, "A", 28, 25, True),
            _completed_game(team, "B", 22, 22, False),
            _completed_game(team, "C", 18, 24, True),
        ])
        db.commit()

        body = client.get(f"/api/v1/teams/{team.id}/standings", headers=admin_headers).json()
        s = body["summary"]
        assert (s["played"], s["wins"], s["draws"], s["losses"]) == (3, 1, 1, 1)
        assert (s["goals_for"], s["goals_against"]) == (28 + 22 + 18, 25 + 22 + 24)
        assert s["goal_difference"] == s["goals_for"] - s["goals_against"]
        assert s["points"] == 2 * 1 + 1 * 1  # 1 win + 1 draw

        opps = {r["opponent"]: r for r in body["per_opponent"]}
        assert opps["A"]["points"] == 2
        assert opps["B"]["points"] == 1
        assert opps["C"]["points"] == 0

    def test_per_opponent_sorted_by_points_then_gd(self, client, db, admin_headers, team):
        # Two opponents same points but different GD; better GD comes first.
        db.add_all([
            _completed_game(team, "X", 30, 20, True),   # win, GD +10
            _completed_game(team, "Y", 22, 21, True),   # win, GD +1
        ])
        db.commit()
        body = client.get(f"/api/v1/teams/{team.id}/standings", headers=admin_headers).json()
        opps = [r["opponent"] for r in body["per_opponent"]]
        assert opps == ["X", "Y"]

    def test_away_game_score_orientation(self, client, db, admin_headers, team):
        # Away game: home_score is opponent's, away_score is the team's.
        # 18 (home/opp) - 21 (away/us) → we won, GF 21 GA 18.
        db.add_all([_completed_game(team, "AwayFC", 18, 21, is_home_game=False)])
        db.commit()
        body = client.get(f"/api/v1/teams/{team.id}/standings", headers=admin_headers).json()
        row = body["per_opponent"][0]
        assert row["goals_for"] == 21
        assert row["goals_against"] == 18
        assert row["wins"] == 1

    def test_date_window_filters(self, client, db, admin_headers, team):
        db.add_all([
            _completed_game(team, "OldFC", 30, 10, True, days_ago=400),   # last season
            _completed_game(team, "NewFC", 25, 20, True, days_ago=10),    # this season
        ])
        db.commit()
        cutoff = (datetime.utcnow() - timedelta(days=90)).isoformat()
        r = client.get(
            f"/api/v1/teams/{team.id}/standings",
            headers=admin_headers,
            params={"from": cutoff},
        )
        opps = [row["opponent"] for row in r.json()["per_opponent"]]
        assert "NewFC" in opps
        assert "OldFC" not in opps

    def test_unrelated_user_gets_403(self, client, db, player_headers, team):
        # Default player_user has no player profile linked to this team.
        r = client.get(f"/api/v1/teams/{team.id}/standings", headers=player_headers)
        assert r.status_code == 403

    def test_missing_team_returns_404(self, client, admin_headers):
        r = client.get("/api/v1/teams/99999/standings", headers=admin_headers)
        assert r.status_code == 404
