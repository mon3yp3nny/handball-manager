"""Registration approval workflow (coach→admin, player/parent→team coach).

Covers: register lands PENDING + routing data; admin self-register blocked;
the approval gate blocking pending users from data endpoints; approve/reject
transitions; approver scoping; and the public team picker.
"""
from app.models.user import User, UserRole, ApprovalStatus
from app.models.player import Player


def _register(client, email, role, team_id=None):
    body = {
        "email": email,
        "password": "testpassword123",
        "first_name": "New",
        "last_name": "Person",
        "role": role,
    }
    if team_id is not None:
        body["requested_team_id"] = team_id
    return client.post("/api/v1/auth/register", json=body)


class TestRegisterPending:
    def test_player_registration_is_pending_and_keeps_team_off_roster(self, client, db, team):
        r = _register(client, "newplayer@test.com", "player", team_id=team.id)
        assert r.status_code == 201
        assert r.json()["approval_status"] == "pending"

        user = db.query(User).filter(User.email == "newplayer@test.com").first()
        assert user.approval_status == ApprovalStatus.PENDING
        assert user.requested_team_id == team.id
        # Player profile exists but is NOT on the team until approved.
        player = db.query(Player).filter(Player.user_id == user.id).first()
        assert player is not None and player.team_id is None

    def test_player_registration_requires_team(self, client):
        r = _register(client, "noteam@test.com", "player")
        assert r.status_code == 400

    def test_coach_registration_is_pending_without_team(self, client):
        r = _register(client, "newcoach@test.com", "coach")
        assert r.status_code == 201
        assert r.json()["approval_status"] == "pending"

    def test_admin_self_registration_forbidden(self, client):
        r = _register(client, "wannabe@test.com", "admin")
        assert r.status_code == 403


class TestApprovalGate:
    def test_pending_user_blocked_from_data_but_sees_status(self, client, db, team):
        _register(client, "pend@test.com", "player", team_id=team.id)
        # Pending users can still authenticate (limited view).
        login = client.post(
            "/api/v1/auth/login",
            data={"username": "pend@test.com", "password": "testpassword123"},
        )
        assert login.status_code == 200
        # /auth/me works and reports pending.
        me = client.get("/api/v1/auth/me")
        assert me.status_code == 200
        assert me.json()["approval_status"] == "pending"
        # A data endpoint is gated.
        assert client.get("/api/v1/teams/").status_code == 403


class TestApproveReject:
    def test_admin_approves_coach(self, client, db, admin_headers):
        _register(client, "coach2@test.com", "coach")
        pending = db.query(User).filter(User.email == "coach2@test.com").first()
        r = client.post(
            f"/api/v1/registrations/{pending.id}/approve", headers=admin_headers
        )
        assert r.status_code == 200
        db.refresh(pending)
        assert pending.approval_status == ApprovalStatus.APPROVED
        assert pending.approved_by_id is not None

    def test_coach_approves_own_team_player_and_assigns_team(
        self, client, db, coach_user, team, coach_headers
    ):
        _register(client, "p2@test.com", "player", team_id=team.id)
        pending = db.query(User).filter(User.email == "p2@test.com").first()
        r = client.post(
            f"/api/v1/registrations/{pending.id}/approve", headers=coach_headers
        )
        assert r.status_code == 200
        player = db.query(Player).filter(Player.user_id == pending.id).first()
        assert player.team_id == team.id

    def test_coach_cannot_approve_player_of_other_team(
        self, client, db, coach_headers, admin_user
    ):
        # A team coached by someone else (admin), not the coach_user.
        from app.models.team import Team
        other = Team(name="Other FC", age_group="U18", coach_id=admin_user.id)
        db.add(other)
        db.commit()
        db.refresh(other)
        _register(client, "p3@test.com", "player", team_id=other.id)
        pending = db.query(User).filter(User.email == "p3@test.com").first()
        r = client.post(
            f"/api/v1/registrations/{pending.id}/approve", headers=coach_headers
        )
        assert r.status_code == 403

    def test_approve_player_whose_team_was_deleted(
        self, client, db, team, admin_headers
    ):
        # Team chosen at sign-up is deleted before approval. requested_team_id
        # is a soft ref; approval must not 500 on the players.team_id FK.
        _register(client, "p4@test.com", "player", team_id=team.id)
        pending = db.query(User).filter(User.email == "p4@test.com").first()
        db.delete(team)
        db.commit()
        r = client.post(
            f"/api/v1/registrations/{pending.id}/approve", headers=admin_headers
        )
        assert r.status_code == 200
        db.refresh(pending)
        assert pending.approval_status == ApprovalStatus.APPROVED
        player = db.query(Player).filter(Player.user_id == pending.id).first()
        assert player.team_id is None  # approved unassigned, no FK blowup

    def test_reject_sets_status_and_reason(self, client, db, admin_headers):
        _register(client, "coach3@test.com", "coach")
        pending = db.query(User).filter(User.email == "coach3@test.com").first()
        r = client.post(
            f"/api/v1/registrations/{pending.id}/reject",
            json={"reason": "Not affiliated with the club"},
            headers=admin_headers,
        )
        assert r.status_code == 200
        db.refresh(pending)
        assert pending.approval_status == ApprovalStatus.REJECTED
        assert pending.rejection_reason == "Not affiliated with the club"

    def test_cannot_act_on_already_decided(self, client, db, admin_headers):
        _register(client, "coach4@test.com", "coach")
        pending = db.query(User).filter(User.email == "coach4@test.com").first()
        client.post(f"/api/v1/registrations/{pending.id}/approve", headers=admin_headers)
        # Second decision → 400 (no longer pending).
        again = client.post(
            f"/api/v1/registrations/{pending.id}/approve", headers=admin_headers
        )
        assert again.status_code == 400


class TestPendingQueueScoping:
    def test_admin_sees_all_coach_sees_own_team_players(
        self, client, db, team, admin_headers, coach_headers
    ):
        _register(client, "qcoach@test.com", "coach")
        _register(client, "qplayer@test.com", "player", team_id=team.id)

        admin_list = client.get("/api/v1/registrations/pending", headers=admin_headers)
        assert admin_list.status_code == 200
        admin_emails = {u["email"] for u in admin_list.json()}
        assert {"qcoach@test.com", "qplayer@test.com"} <= admin_emails

        coach_list = client.get("/api/v1/registrations/pending", headers=coach_headers)
        assert coach_list.status_code == 200
        coach_emails = {u["email"] for u in coach_list.json()}
        assert "qplayer@test.com" in coach_emails  # their team's player
        assert "qcoach@test.com" not in coach_emails  # not a coach's concern


class TestPublicTeams:
    def test_public_team_picker_no_auth(self, client, team):
        r = client.get("/api/v1/teams/public")
        assert r.status_code == 200
        items = r.json()
        assert any(t["id"] == team.id and t["name"] == team.name for t in items)
