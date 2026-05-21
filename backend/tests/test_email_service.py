"""Tests for the EmailService and its endpoint wiring (#48)."""
import asyncio
from unittest.mock import AsyncMock, patch

import pytest

from app.services.email_service import EmailService


@pytest.fixture()
def service(monkeypatch):
    """Fresh EmailService with dry-run forced ON so tests never try SMTP."""
    monkeypatch.setattr("app.services.email_service.settings.EMAIL_DRY_RUN", True)
    monkeypatch.setattr("app.services.email_service.settings.SMTP_HOST", None)
    return EmailService()


def _run(coro):
    return asyncio.get_event_loop().run_until_complete(coro) if False else asyncio.run(coro)


class TestTemplateRendering:
    """Catches the regression where Template() without an Environment
    couldn't resolve `{% extends "base.html" %}`."""

    def test_html_template_renders_with_extends(self, service):
        out = service._render_template("welcome", {"first_name": "Test", "login_link": "https://x"})
        assert "<html" in out  # base.html wrapper present
        assert "Test" in out
        assert 'class="button"' in out  # styles from base inherited

    def test_text_fallback_renders(self, service):
        out = service._render_template("welcome", {"first_name": "Test", "login_link": "https://x"}, text_fallback=True)
        assert "Hallo Test" in out
        assert "<html" not in out  # plain text, no HTML wrapper

    def test_password_reset_templates_exist(self, service):
        html = service._render_template("password_reset", {"first_name": "Anna", "reset_link": "https://x/r?t=abc", "expires_in": "1 Stunde"})
        assert "Anna" in html
        assert "https://x/r?t=abc" in html
        assert "1 Stunde" in html

    def test_missing_template_returns_safe_string(self, service):
        out = service._render_template("does_not_exist", {})
        assert "not found" in out.lower()


class TestDryRunMode:
    """Without SMTP configured, _send_email must return True + log,
    never raise."""

    def test_send_welcome_in_dry_run(self, service, caplog):
        with caplog.at_level("INFO"):
            ok = _run(service.send_welcome_email("u@x.test", "Anna"))
        assert ok is True
        joined = "\n".join(r.message for r in caplog.records)
        assert "DRY-RUN" in joined
        assert "u@x.test" in joined

    def test_send_password_reset_in_dry_run(self, service):
        ok = _run(
            service.send_password_reset_email(
                "u@x.test", "Anna", "https://x/reset?token=abc",
            )
        )
        assert ok is True

    def test_send_test_email_in_dry_run(self, service):
        ok = _run(service.send_test_email("u@x.test"))
        assert ok is True


class TestSMTPPathSendsViaFastMail:
    """When SMTP is configured, fastapi-mail is invoked and the dry-run
    branch is skipped. Patch FastMail itself so the test isn't hostage
    to a real SMTP server."""

    def test_smtp_path_calls_send_message(self, monkeypatch):
        monkeypatch.setattr("app.services.email_service.settings.EMAIL_DRY_RUN", False)
        monkeypatch.setattr("app.services.email_service.settings.SMTP_HOST", "smtp.test")
        monkeypatch.setattr("app.services.email_service.settings.SMTP_USER", "u")
        monkeypatch.setattr("app.services.email_service.settings.SMTP_PASSWORD", "p")
        svc = EmailService()

        fake_fm = AsyncMock()
        # Skip _get_fastmail so ConnectionConfig isn't constructed in the test.
        monkeypatch.setattr(svc, "_get_fastmail", lambda: fake_fm)
        # fastapi-mail's MessageSchema validates recipients and rejects
        # reserved TLDs like .test, so use a real-looking address here.
        ok = _run(svc.send_test_email("ops@example.com"))
        assert ok is True
        fake_fm.send_message.assert_awaited_once()


class TestForgotPasswordEndpoint:
    """The forgot-password endpoint must not reveal whether an email
    exists, and on a known email it should queue a send."""

    def test_unknown_email_returns_generic_message(self, client):
        r = client.post("/api/v1/auth/forgot-password", json={"email": "nope@x.test"})
        assert r.status_code == 200
        assert "If the email exists" in r.json()["message"]

    def test_known_email_returns_same_generic_message(self, client, player_user):
        r = client.post("/api/v1/auth/forgot-password", json={"email": player_user.email})
        assert r.status_code == 200
        assert "If the email exists" in r.json()["message"]

    def test_missing_email_returns_400(self, client):
        r = client.post("/api/v1/auth/forgot-password", json={})
        assert r.status_code == 400


class TestEmailTestEndpoint:
    """POST /auth/email/test is admin-only and queues a dry-run send."""

    def test_admin_can_queue_test_email(self, client, admin_headers):
        r = client.post(
            "/api/v1/auth/email/test",
            headers=admin_headers,
            json={"to": "ops@x.test"},
        )
        assert r.status_code == 202
        body = r.json()
        assert "ops@x.test" in body["message"]
        assert "dry_run" in body

    def test_coach_forbidden(self, client, coach_headers):
        r = client.post(
            "/api/v1/auth/email/test",
            headers=coach_headers,
            json={"to": "ops@x.test"},
        )
        assert r.status_code == 403

    def test_missing_to_400(self, client, admin_headers):
        r = client.post(
            "/api/v1/auth/email/test",
            headers=admin_headers,
            json={},
        )
        assert r.status_code == 400
