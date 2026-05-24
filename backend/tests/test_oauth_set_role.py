"""Tests for the OAuth /set-role endpoint guards (#88).

Covers self-service privilege-escalation defenses without exercising
the Google/Apple token verification path (which is mocked elsewhere).
"""
from app.core.security import create_access_token
from app.models.user import User, UserRole


def _make_oauth_user(db, *, email, role=UserRole.PLAYER, role_selected=False):
    user = User(
        email=email,
        hashed_password=None,
        first_name="OAuth",
        last_name="User",
        role=role,
        is_active=True,
        is_verified=True,
        is_oauth_only=True,
        role_selected=role_selected,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def _headers(user):
    token = create_access_token(data={"sub": user.email, "role": user.role.value})
    return {"Authorization": f"Bearer {token}"}


class TestSetRoleFirstTime:
    def test_oauth_user_can_set_role_once(self, client, db):
        user = _make_oauth_user(db, email="newoauth@test.com")
        resp = client.post(
            "/api/v1/oauth/set-role",
            json={"role": "coach"},
            headers=_headers(user),
        )
        assert resp.status_code == 200
        db.refresh(user)
        assert user.role == UserRole.COACH
        assert user.role_selected is True


class TestSetRoleApprovalParity:
    """OAuth sign-ups must go through the same approval gate as password
    registration — choosing a non-admin role drops them into PENDING."""

    def test_coach_role_becomes_pending(self, client, db):
        from app.models.user import ApprovalStatus
        user = _make_oauth_user(db, email="oauthcoach@test.com")
        resp = client.post(
            "/api/v1/oauth/set-role",
            json={"role": "coach"},
            headers=_headers(user),
        )
        assert resp.status_code == 200
        assert resp.json()["approval_status"] == "pending"
        db.refresh(user)
        assert user.approval_status == ApprovalStatus.PENDING

    def test_player_role_requires_team(self, client, db):
        user = _make_oauth_user(db, email="oauthplayer@test.com")
        resp = client.post(
            "/api/v1/oauth/set-role",
            json={"role": "player"},
            headers=_headers(user),
        )
        assert resp.status_code == 400

    def test_player_role_with_team_pends_and_creates_profile(self, client, db):
        from app.models.user import ApprovalStatus
        from app.models.player import Player
        from app.models.team import Team
        team = Team(name="OAuth FC", age_group="U14")
        db.add(team)
        db.commit()
        db.refresh(team)

        user = _make_oauth_user(db, email="oauthplayer2@test.com")
        resp = client.post(
            "/api/v1/oauth/set-role",
            json={"role": "player", "requested_team_id": team.id},
            headers=_headers(user),
        )
        assert resp.status_code == 200
        db.refresh(user)
        assert user.approval_status == ApprovalStatus.PENDING
        assert user.requested_team_id == team.id
        # Player profile created, unattached until approval.
        player = db.query(Player).filter(Player.user_id == user.id).first()
        assert player is not None and player.team_id is None


class TestSetRoleEscalationBlocked:
    def test_cannot_set_role_twice(self, client, db):
        """Regression for #88: once role_selected=true the endpoint refuses."""
        user = _make_oauth_user(
            db, email="already@test.com", role=UserRole.PLAYER, role_selected=True,
        )
        resp = client.post(
            "/api/v1/oauth/set-role",
            json={"role": "admin"},
            headers=_headers(user),
        )
        assert resp.status_code == 403
        assert "already been selected" in resp.json()["detail"]
        db.refresh(user)
        assert user.role == UserRole.PLAYER

    def test_cannot_self_assign_admin_even_first_time(self, client, db):
        """Regression for #88: admin must never come from self-service flow."""
        user = _make_oauth_user(db, email="wannabe-admin@test.com")
        resp = client.post(
            "/api/v1/oauth/set-role",
            json={"role": "admin"},
            headers=_headers(user),
        )
        assert resp.status_code == 403
        assert "Admin" in resp.json()["detail"]
        db.refresh(user)
        assert user.role == UserRole.PLAYER
        assert user.role_selected is False

    def test_password_user_rejected(self, client, db):
        """Non-OAuth users must not use this endpoint at all."""
        from tests.conftest import _make_user, _auth_header
        user = _make_user(db, email="password@test.com", role=UserRole.PLAYER)
        resp = client.post(
            "/api/v1/oauth/set-role",
            json={"role": "coach"},
            headers=_auth_header(user),
        )
        assert resp.status_code == 400
