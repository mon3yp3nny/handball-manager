"""Tests for the shared can_access_team helper.

This is the authorization logic reused by GET /teams/{id} (#86) and the
WebSocket subscribe_team handler (#87), so unit-testing it directly covers
the security-critical path for both fixes.
"""
from app.core.permissions import can_access_team
from app.models.user import UserRole
from tests.conftest import _make_user


class TestCanAccessTeam:
    def test_admin_allowed(self, db, admin_user, team):
        assert can_access_team(admin_user, team.id, db) is True

    def test_supervisor_allowed(self, db, supervisor_user, team):
        assert can_access_team(supervisor_user, team.id, db) is True

    def test_owning_coach_allowed(self, db, coach_user, team):
        assert can_access_team(coach_user, team.id, db) is True

    def test_other_coach_denied(self, db, team):
        other = _make_user(db, email="other2.coach@test.com", role=UserRole.COACH)
        assert can_access_team(other, team.id, db) is False

    def test_player_on_team_allowed(self, db, player_user, team, player_profile):
        assert can_access_team(player_user, team.id, db) is True

    def test_player_without_profile_denied(self, db, player_user, team):
        assert can_access_team(player_user, team.id, db) is False

    def test_parent_of_child_on_team_allowed(
        self, db, parent_user, team, parent_child_link
    ):
        assert can_access_team(parent_user, team.id, db) is True

    def test_unrelated_parent_denied(self, db, parent_user, team):
        assert can_access_team(parent_user, team.id, db) is False
