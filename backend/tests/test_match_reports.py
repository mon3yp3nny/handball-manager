"""Tests for the match-report endpoints (#131)."""
from datetime import datetime, timedelta


def _completed_game(db, team, opponent="Foo FC", score=(25, 22)):
    from app.models.game import Game, GameStatus
    g = Game(
        team_id=team.id,
        opponent=opponent,
        location="Halle",
        scheduled_at=datetime.utcnow() - timedelta(days=1),
        status=GameStatus.COMPLETED,
        home_score=score[0],
        away_score=score[1],
        is_home_game=True,
    )
    db.add(g)
    db.commit()
    return g


class TestMatchReport:
    def test_coach_creates_and_reads(self, client, db, coach_headers, team):
        g = _completed_game(db, team)
        r = client.post(
            f"/api/v1/games/{g.id}/report",
            headers=coach_headers,
            json={"body": "Solides Spiel, kompakte Abwehr.", "man_of_the_match_player_id": None},
        )
        assert r.status_code == 201
        body = r.json()
        assert body["body"].startswith("Solides")
        # Re-read works.
        r2 = client.get(f"/api/v1/games/{g.id}/report", headers=coach_headers)
        assert r2.status_code == 200
        assert r2.json()["id"] == body["id"]

    def test_one_report_per_game(self, client, db, coach_headers, team):
        g = _completed_game(db, team)
        client.post(
            f"/api/v1/games/{g.id}/report",
            headers=coach_headers,
            json={"body": "First write-up"},
        )
        r = client.post(
            f"/api/v1/games/{g.id}/report",
            headers=coach_headers,
            json={"body": "Second write-up"},
        )
        assert r.status_code == 409

    def test_put_updates(self, client, db, coach_headers, team):
        g = _completed_game(db, team)
        client.post(
            f"/api/v1/games/{g.id}/report",
            headers=coach_headers,
            json={"body": "First"},
        )
        r = client.put(
            f"/api/v1/games/{g.id}/report",
            headers=coach_headers,
            json={"body": "Updated narrative"},
        )
        assert r.status_code == 200
        assert r.json()["body"] == "Updated narrative"

    def test_mom_must_be_on_team(self, client, db, coach_headers, team, player_user):
        from app.models.player import Player
        from app.models.team import Team

        # Other-team player
        other = Team(name="Other")
        db.add(other)
        db.commit()
        # The seeded player_user has no profile; give them one on `other`.
        op = Player(user_id=player_user.id, team_id=other.id)
        db.add(op)
        db.commit()

        g = _completed_game(db, team)
        r = client.post(
            f"/api/v1/games/{g.id}/report",
            headers=coach_headers,
            json={"body": "x", "man_of_the_match_player_id": op.id},
        )
        assert r.status_code == 400

    def test_player_reads_team_report(self, client, db, coach_headers, player_headers, team, player_user):
        from app.models.player import Player

        # Put the seeded player on the same team so they have access.
        db.add(Player(user_id=player_user.id, team_id=team.id))
        db.commit()

        g = _completed_game(db, team)
        client.post(
            f"/api/v1/games/{g.id}/report",
            headers=coach_headers,
            json={"body": "Team write-up"},
        )
        r = client.get(f"/api/v1/games/{g.id}/report", headers=player_headers)
        assert r.status_code == 200
        assert r.json()["body"] == "Team write-up"

    def test_get_404_when_missing(self, client, db, coach_headers, team):
        g = _completed_game(db, team)
        r = client.get(f"/api/v1/games/{g.id}/report", headers=coach_headers)
        assert r.status_code == 404
