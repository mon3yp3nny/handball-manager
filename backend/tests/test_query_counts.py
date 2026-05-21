"""N+1 regression tests (#62).

Eager-loading is invisible — turn it off and tests still pass, the
endpoint just gets slower as the dataset grows. These tests count the
SQL queries issued per request against a deliberately larger seed than
the rest of the suite uses, so a regression on `selectinload` shows up
as "this used to take 4 queries, now it takes 24".

The bounds are loose on purpose: we assert query count grows by O(1)
not O(N). Bumping these intentionally is fine; flipping them silently
isn't.
"""
from contextlib import contextmanager
from datetime import date, datetime, timedelta

import pytest
from sqlalchemy import event

from app.core.security import get_password_hash
from app.models.attendance import Attendance, AttendanceStatus
from app.models.game import Game, GameStatus
from app.models.parent_child import ParentChild
from app.models.player import Player, Position
from app.models.user import User, UserRole


@contextmanager
def count_queries(engine):
    """Yield a list that fills with each statement issued for the
    lifetime of the context. We attach to the engine the test fixture
    is using (in-memory SQLite from conftest)."""
    statements: list[str] = []

    def _on_exec(conn, cursor, statement, parameters, context, executemany):
        statements.append(statement)

    event.listen(engine, "before_cursor_execute", _on_exec)
    try:
        yield statements
    finally:
        event.remove(engine, "before_cursor_execute", _on_exec)


@pytest.fixture()
def busy_dataset(db):
    """Seed enough rows that an N+1 would be obvious — 20 players on
    one team so the players list query count jumps from O(1) to O(20)
    if eager loading is removed."""
    coach = User(
        email="qcoach@test.com",
        hashed_password=get_password_hash("x"),
        first_name="Q", last_name="C", role=UserRole.COACH, is_active=True,
    )
    db.add(coach)
    db.flush()
    from app.models.team import Team
    team = Team(name="Query Team", coach_id=coach.id)
    db.add(team); db.flush()

    players: list[Player] = []
    for i in range(20):
        u = User(
            email=f"q{i}@test.com",
            hashed_password=get_password_hash("x"),
            first_name=f"P{i}", last_name="X",
            role=UserRole.PLAYER, is_active=True,
        )
        db.add(u); db.flush()
        p = Player(
            user_id=u.id, team_id=team.id,
            jersey_number=i + 1, position=Position.PIVOT,
            # Spread birthdays so some land in the next-7-days window.
            date_of_birth=date(2008, ((i + date.today().month - 1) % 12) + 1, ((i + date.today().day - 1) % 27) + 1),
        )
        db.add(p); players.append(p)
    db.flush()

    # A handful of past games + events for the attendance / dashboard hits.
    games = []
    for i in range(5):
        g = Game(
            team_id=team.id, opponent=f"Op{i}", location="Halle",
            scheduled_at=datetime.utcnow() - timedelta(days=7 * (i + 1)),
            status=GameStatus.COMPLETED, is_home_game=(i % 2 == 0),
            home_score=25, away_score=22,
        )
        db.add(g); games.append(g)
    db.flush()
    for g in games:
        for p in players[:5]:
            db.add(Attendance(
                player_id=p.id, game_id=g.id,
                status=AttendanceStatus.PRESENT, recorded_by=coach.id,
            ))
    db.commit()
    return {"team": team, "players": players, "coach": coach}


# Bounds chosen with comfortable headroom over the current numbers
# (probed in the original audit) so this isn't fragile against unrelated
# refactors but still catches obvious regressions.
class TestListEndpointsAreBounded:
    def test_players_list_is_bounded(self, client, admin_headers, busy_dataset, db):
        engine = db.get_bind()
        with count_queries(engine) as queries:
            r = client.get("/api/v1/players/?limit=100", headers=admin_headers)
        assert r.status_code == 200
        assert len(r.json()["items"]) >= 20
        # Pre-fix this was 23 queries (1 + 1 per player). 6 is generous
        # but tight enough to fail if the selectinload disappears.
        assert len(queries) < 6, (
            f"players list issued {len(queries)} queries; selectinload(Player.user) likely lost. "
            f"Bumping this above 6 means a real N+1."
        )

    def test_team_detail_is_bounded(self, client, admin_headers, busy_dataset):
        team = busy_dataset["team"]
        with count_queries(client.app.dependency_overrides_engine if False else _engine_from(client)) as queries:
            r = client.get(f"/api/v1/teams/{team.id}", headers=admin_headers)
        assert r.status_code == 200
        # joinedload(Team.players).joinedload(Player.user) — one query
        # should bring everything back.
        assert len(queries) <= 4

    def test_dashboard_widgets_bounded(self, client, admin_headers, busy_dataset, db):
        engine = db.get_bind()
        with count_queries(engine) as queries:
            r = client.get("/api/v1/dashboard/widgets", headers=admin_headers)
        assert r.status_code == 200
        # next_match + visible_team_ids + birthday players + selectinload(user)
        assert len(queries) < 8

    def test_attendance_list_bounded(self, client, admin_headers, busy_dataset, db):
        engine = db.get_bind()
        with count_queries(engine) as queries:
            r = client.get("/api/v1/attendance/?limit=100", headers=admin_headers)
        assert r.status_code == 200
        assert len(queries) < 6


def _engine_from(client):
    # Reach into the test client's overridden get_db to find the engine.
    # conftest's TestingSessionLocal is bound to the in-memory engine.
    from app.db.session import get_db
    gen = client.app.dependency_overrides[get_db]()
    s = next(gen)
    try:
        return s.get_bind()
    finally:
        try:
            next(gen)
        except StopIteration:
            pass
