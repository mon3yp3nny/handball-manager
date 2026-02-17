"""Tests for input validation via Pydantic schema constraints."""


class TestUserValidation:
    def test_short_password_rejected(self, client, admin_headers):
        resp = client.post(
            "/api/v1/users/",
            headers=admin_headers,
            json={
                "email": "val@test.com",
                "password": "short",
                "first_name": "V",
                "last_name": "U",
                "role": "player",
            },
        )
        assert resp.status_code == 422

    def test_invalid_email_rejected(self, client, admin_headers):
        resp = client.post(
            "/api/v1/users/",
            headers=admin_headers,
            json={
                "email": "not-an-email",
                "password": "securepass123",
                "first_name": "V",
                "last_name": "U",
                "role": "player",
            },
        )
        assert resp.status_code == 422

    def test_empty_first_name_rejected(self, client, admin_headers):
        resp = client.post(
            "/api/v1/users/",
            headers=admin_headers,
            json={
                "email": "empty@test.com",
                "password": "securepass123",
                "first_name": "",
                "last_name": "User",
                "role": "player",
            },
        )
        assert resp.status_code == 422

    def test_invalid_phone_rejected(self, client, admin_headers):
        resp = client.post(
            "/api/v1/users/",
            headers=admin_headers,
            json={
                "email": "phone@test.com",
                "password": "securepass123",
                "first_name": "P",
                "last_name": "U",
                "phone": "abc",
                "role": "player",
            },
        )
        assert resp.status_code == 422


class TestTeamValidation:
    def test_empty_team_name_rejected(self, client, coach_headers):
        resp = client.post(
            "/api/v1/teams/",
            headers=coach_headers,
            json={"name": ""},
        )
        assert resp.status_code == 422


class TestPlayerValidation:
    def test_jersey_number_out_of_range(self, client, coach_headers, db):
        from tests.conftest import _make_user
        from app.models.user import UserRole

        user = _make_user(db, email="jersey@test.com", role=UserRole.PLAYER)
        resp = client.post(
            "/api/v1/players/",
            headers=coach_headers,
            json={"user_id": user.id, "jersey_number": 100},
        )
        assert resp.status_code == 422

    def test_jersey_number_zero(self, client, coach_headers, db):
        from tests.conftest import _make_user
        from app.models.user import UserRole

        user = _make_user(db, email="zero@test.com", role=UserRole.PLAYER)
        resp = client.post(
            "/api/v1/players/",
            headers=coach_headers,
            json={"user_id": user.id, "jersey_number": 0},
        )
        assert resp.status_code == 422


class TestGameValidation:
    def test_negative_score_rejected(self, client, coach_headers, game):
        resp = client.patch(
            f"/api/v1/games/{game.id}/result",
            headers=coach_headers,
            json={"home_score": -1, "away_score": 0},
        )
        assert resp.status_code == 422


class TestNewsValidation:
    def test_empty_title_rejected(self, client, coach_headers):
        resp = client.post(
            "/api/v1/news/",
            headers=coach_headers,
            json={"title": "", "content": "body"},
        )
        assert resp.status_code == 422

    def test_empty_content_rejected(self, client, coach_headers):
        resp = client.post(
            "/api/v1/news/",
            headers=coach_headers,
            json={"title": "Title", "content": ""},
        )
        assert resp.status_code == 422


class TestInvitationValidation:
    def test_invalid_role(self, client, coach_headers, team):
        resp = client.post(
            "/api/v1/invitations/send",
            headers=coach_headers,
            json={
                "email": "val@test.com",
                "first_name": "V",
                "last_name": "U",
                "role": "hacker",
                "team_id": team.id,
            },
        )
        assert resp.status_code == 422
