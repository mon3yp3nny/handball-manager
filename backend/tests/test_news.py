"""Tests for News CRUD endpoints."""
from tests.conftest import _make_user, _auth_header
from app.models.user import UserRole


class TestGetNews:
    def test_admin_lists_news(self, client, admin_headers, news_item):
        resp = client.get("/api/v1/news/", headers=admin_headers)
        assert resp.status_code == 200
        assert len(resp.json()) >= 1

    def test_coach_lists_news(self, client, coach_headers, news_item):
        resp = client.get("/api/v1/news/", headers=coach_headers)
        assert resp.status_code == 200

    def test_unauthenticated(self, client):
        resp = client.get("/api/v1/news/")
        assert resp.status_code == 401


class TestCreateNews:
    def test_coach_creates_news(self, client, coach_headers, team):
        resp = client.post(
            "/api/v1/news/",
            headers=coach_headers,
            json={
                "title": "Headline",
                "content": "Body text here",
                "team_id": team.id,
            },
        )
        assert resp.status_code == 201
        assert resp.json()["title"] == "Headline"

    def test_supervisor_creates_news(self, client, supervisor_headers, team):
        resp = client.post(
            "/api/v1/news/",
            headers=supervisor_headers,
            json={
                "title": "Supervisor News",
                "content": "Important update",
                "team_id": team.id,
            },
        )
        assert resp.status_code == 201

    def test_player_cannot_create_news(self, client, player_headers, team):
        resp = client.post(
            "/api/v1/news/",
            headers=player_headers,
            json={"title": "Nope", "content": "Blocked"},
        )
        assert resp.status_code == 403

    def test_create_global_news(self, client, coach_headers):
        resp = client.post(
            "/api/v1/news/",
            headers=coach_headers,
            json={"title": "Global", "content": "Everyone sees this"},
        )
        assert resp.status_code == 201
        assert resp.json()["team_id"] is None


class TestGetNewsItem:
    def test_get_news_by_id(self, client, coach_headers, news_item):
        resp = client.get(f"/api/v1/news/{news_item.id}", headers=coach_headers)
        assert resp.status_code == 200
        assert resp.json()["id"] == news_item.id

    def test_get_nonexistent(self, client, coach_headers):
        resp = client.get("/api/v1/news/99999", headers=coach_headers)
        assert resp.status_code == 404


class TestUpdateNews:
    def test_author_updates_news(self, client, coach_headers, news_item):
        resp = client.put(
            f"/api/v1/news/{news_item.id}",
            headers=coach_headers,
            json={"title": "Updated Title"},
        )
        assert resp.status_code == 200
        assert resp.json()["title"] == "Updated Title"

    def test_non_author_cannot_update(self, client, db, news_item):
        other = _make_user(db, email="othercoach@test.com", role=UserRole.COACH)
        headers = _auth_header(other)
        resp = client.put(
            f"/api/v1/news/{news_item.id}",
            headers=headers,
            json={"title": "Hacked"},
        )
        assert resp.status_code == 403


class TestPublishNews:
    def test_publish(self, client, coach_headers, news_item):
        resp = client.patch(
            f"/api/v1/news/{news_item.id}/publish",
            headers=coach_headers,
            json={"is_published": True},
        )
        assert resp.status_code == 200
        assert resp.json()["is_published"] is True

    def test_unpublish(self, client, coach_headers, news_item):
        resp = client.patch(
            f"/api/v1/news/{news_item.id}/publish",
            headers=coach_headers,
            json={"is_published": False},
        )
        assert resp.status_code == 200
        assert resp.json()["is_published"] is False


class TestDeleteNews:
    def test_author_deletes_news(self, client, coach_headers, news_item):
        resp = client.delete(f"/api/v1/news/{news_item.id}", headers=coach_headers)
        assert resp.status_code == 204

    def test_player_cannot_delete_news(self, client, player_headers, news_item):
        resp = client.delete(f"/api/v1/news/{news_item.id}", headers=player_headers)
        assert resp.status_code == 403
