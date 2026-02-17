"""Shared test fixtures for the handball-manager backend test suite."""
import os
import sys
import pytest
from datetime import datetime, timedelta

# Set test environment variables BEFORE any app imports
os.environ["DATABASE_URL"] = "sqlite:///./test.db"
os.environ["SECRET_KEY"] = "test-secret-key-not-for-production-use"
os.environ["FRONTEND_URL"] = "http://localhost:3000"

from sqlalchemy import create_engine, event as sa_event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

from app.db.session import Base, get_db
from app.core.security import create_access_token, create_refresh_token, get_password_hash
from app.models.user import User, UserRole
from app.models.team import Team
from app.models.player import Player
from app.models.parent_child import ParentChild
from app.models.game import Game, GameStatus, GameType
from app.models.event import Event, EventType
from app.models.attendance import Attendance, AttendanceStatus
from app.models.news import News
from app.models.invitation import Invitation, InvitationStatus
from app.main import app


# ---------------------------------------------------------------------------
# Database fixtures
# ---------------------------------------------------------------------------

SQLALCHEMY_TEST_DATABASE_URL = "sqlite://"

test_engine = create_engine(
    SQLALCHEMY_TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)


# Enable foreign-key enforcement for SQLite
@sa_event.listens_for(test_engine, "connect")
def _set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture(autouse=True)
def db():
    """Create a clean database for every test."""
    Base.metadata.create_all(bind=test_engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=test_engine)


@pytest.fixture()
def client(db):
    """FastAPI TestClient with the test database injected."""

    def _override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = _override_get_db
    with TestClient(app, raise_server_exceptions=False) as c:
        yield c
    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# User helpers
# ---------------------------------------------------------------------------


def _make_user(
    db, *, email, role, first_name="Test", last_name="User", password="testpassword123"
):
    user = User(
        email=email,
        hashed_password=get_password_hash(password),
        first_name=first_name,
        last_name=last_name,
        role=role,
        is_active=True,
        is_verified=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def _make_token(user):
    return create_access_token(data={"sub": user.email, "role": user.role.value})


def _auth_header(user):
    return {"Authorization": f"Bearer {_make_token(user)}"}


# ---------------------------------------------------------------------------
# User fixtures (one per role)
# ---------------------------------------------------------------------------


@pytest.fixture()
def admin_user(db):
    return _make_user(
        db, email="admin@test.com", role=UserRole.ADMIN, first_name="Admin", last_name="Boss"
    )


@pytest.fixture()
def coach_user(db):
    return _make_user(
        db, email="coach@test.com", role=UserRole.COACH, first_name="Coach", last_name="Smith"
    )


@pytest.fixture()
def supervisor_user(db):
    return _make_user(
        db,
        email="supervisor@test.com",
        role=UserRole.SUPERVISOR,
        first_name="Super",
        last_name="Visor",
    )


@pytest.fixture()
def player_user(db):
    return _make_user(
        db, email="player@test.com", role=UserRole.PLAYER, first_name="Player", last_name="One"
    )


@pytest.fixture()
def parent_user(db):
    return _make_user(
        db, email="parent@test.com", role=UserRole.PARENT, first_name="Parent", last_name="Doe"
    )


# ---------------------------------------------------------------------------
# Auth header fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def admin_headers(admin_user):
    return _auth_header(admin_user)


@pytest.fixture()
def coach_headers(coach_user):
    return _auth_header(coach_user)


@pytest.fixture()
def supervisor_headers(supervisor_user):
    return _auth_header(supervisor_user)


@pytest.fixture()
def player_headers(player_user):
    return _auth_header(player_user)


@pytest.fixture()
def parent_headers(parent_user):
    return _auth_header(parent_user)


# ---------------------------------------------------------------------------
# Domain-object fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def team(db, coach_user):
    t = Team(name="Test Handball FC", age_group="U16", coach_id=coach_user.id)
    db.add(t)
    db.commit()
    db.refresh(t)
    return t


@pytest.fixture()
def player_profile(db, player_user, team):
    p = Player(user_id=player_user.id, team_id=team.id, jersey_number=7, position="left_wing")
    db.add(p)
    db.commit()
    db.refresh(p)
    return p


@pytest.fixture()
def parent_child_link(db, parent_user, player_profile):
    link = ParentChild(parent_id=parent_user.id, child_id=player_profile.id)
    db.add(link)
    db.commit()
    db.refresh(link)
    return link


@pytest.fixture()
def game(db, team):
    g = Game(
        team_id=team.id,
        opponent="Rival FC",
        location="Home Arena",
        scheduled_at=datetime.utcnow() + timedelta(days=3),
        game_type=GameType.LEAGUE,
        status=GameStatus.SCHEDULED,
        is_home_game=True,
    )
    db.add(g)
    db.commit()
    db.refresh(g)
    return g


@pytest.fixture()
def event_obj(db, team):
    e = Event(
        title="Morning Training",
        team_id=team.id,
        event_type=EventType.TRAINING,
        location="Training Field",
        start_time=datetime.utcnow() + timedelta(days=1),
        end_time=datetime.utcnow() + timedelta(days=1, hours=2),
    )
    db.add(e)
    db.commit()
    db.refresh(e)
    return e


@pytest.fixture()
def news_item(db, coach_user, team):
    n = News(
        title="Big Win",
        content="We won the game!",
        team_id=team.id,
        author_id=coach_user.id,
        is_published=True,
        published_at=datetime.utcnow(),
    )
    db.add(n)
    db.commit()
    db.refresh(n)
    return n


@pytest.fixture()
def attendance_record(db, player_profile, game):
    a = Attendance(
        player_id=player_profile.id,
        game_id=game.id,
        status=AttendanceStatus.PENDING,
    )
    db.add(a)
    db.commit()
    db.refresh(a)
    return a
