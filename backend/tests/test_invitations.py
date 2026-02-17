"""Tests for Invitation endpoints."""
import uuid
from datetime import datetime, timedelta
from tests.conftest import _make_user, _auth_header
from app.models.user import UserRole
from app.models.invitation import Invitation, InvitationStatus


class TestSendInvitation:
    def test_coach_sends_invitation(self, client, coach_headers, team):
        resp = client.post(
            "/api/v1/invitations/send",
            headers=coach_headers,
            json={
                "email": "invited@test.com",
                "first_name": "New",
                "last_name": "Player",
                "role": "player",
                "team_id": team.id,
            },
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["email"] == "invited@test.com"
        assert body["status"] == "pending"

    def test_admin_sends_invitation(self, client, admin_headers, team):
        resp = client.post(
            "/api/v1/invitations/send",
            headers=admin_headers,
            json={
                "email": "admin_invite@test.com",
                "first_name": "Admin",
                "last_name": "Invite",
                "role": "parent",
                "team_id": team.id,
            },
        )
        assert resp.status_code == 200

    def test_player_cannot_send_invitation(self, client, player_headers, team):
        resp = client.post(
            "/api/v1/invitations/send",
            headers=player_headers,
            json={
                "email": "nope@test.com",
                "first_name": "No",
                "last_name": "Way",
                "role": "player",
                "team_id": team.id,
            },
        )
        assert resp.status_code == 403

    def test_invite_existing_email_rejected(self, client, coach_headers, team, admin_user):
        resp = client.post(
            "/api/v1/invitations/send",
            headers=coach_headers,
            json={
                "email": admin_user.email,
                "first_name": "Dup",
                "last_name": "User",
                "role": "player",
                "team_id": team.id,
            },
        )
        assert resp.status_code == 400
        assert "already exists" in resp.json()["detail"]

    def test_invite_nonexistent_team(self, client, coach_headers):
        resp = client.post(
            "/api/v1/invitations/send",
            headers=coach_headers,
            json={
                "email": "noteam@test.com",
                "first_name": "No",
                "last_name": "Team",
                "role": "player",
                "team_id": 99999,
            },
        )
        assert resp.status_code == 404


class TestGetSentInvitations:
    def test_coach_sees_own_invitations(self, client, coach_headers, db, coach_user, team):
        inv = Invitation(
            email="sent1@test.com",
            first_name="S",
            last_name="One",
            role="player",
            team_id=team.id,
            invited_by=coach_user.id,
        )
        db.add(inv)
        db.commit()
        resp = client.get("/api/v1/invitations/sent", headers=coach_headers)
        assert resp.status_code == 200
        body = resp.json()
        assert body["total"] >= 1


class TestVerifyInvitation:
    def test_verify_valid_token(self, client, db, coach_user, team):
        inv = Invitation(
            email="verify@test.com",
            first_name="V",
            last_name="User",
            role="player",
            team_id=team.id,
            invited_by=coach_user.id,
        )
        db.add(inv)
        db.commit()
        db.refresh(inv)
        resp = client.get(f"/api/v1/invitations/verify/{inv.token}")
        assert resp.status_code == 200
        assert resp.json()["valid"] is True

    def test_verify_invalid_token(self, client):
        resp = client.get("/api/v1/invitations/verify/fake-token-123")
        assert resp.status_code == 200
        assert resp.json()["valid"] is False

    def test_verify_expired_invitation(self, client, db, coach_user, team):
        token = str(uuid.uuid4())
        inv = Invitation(
            email="expired@test.com",
            first_name="E",
            last_name="User",
            role="player",
            team_id=team.id,
            invited_by=coach_user.id,
            token=token,
            expires_at=datetime.utcnow() - timedelta(days=1),
        )
        db.add(inv)
        db.commit()
        resp = client.get(f"/api/v1/invitations/verify/{token}")
        assert resp.status_code == 200
        assert resp.json()["valid"] is False


class TestRevokeInvitation:
    def test_coach_revokes_invitation(self, client, coach_headers, db, coach_user, team):
        inv = Invitation(
            email="revoke@test.com",
            first_name="R",
            last_name="User",
            role="player",
            team_id=team.id,
            invited_by=coach_user.id,
        )
        db.add(inv)
        db.commit()
        db.refresh(inv)
        resp = client.delete(
            f"/api/v1/invitations/{inv.id}", headers=coach_headers
        )
        assert resp.status_code == 204

    def test_cannot_revoke_nonexistent(self, client, coach_headers):
        resp = client.delete("/api/v1/invitations/99999", headers=coach_headers)
        assert resp.status_code == 404
