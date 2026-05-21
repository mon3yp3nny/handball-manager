"""Sentry observability tests (#64).

We can't (and don't want to) actually ship events to Sentry's servers
during tests, so we exercise the pure parts: the `init_sentry()`
no-op-without-DSN contract, and the `_before_send` filter that decides
which events leave the box.
"""
from __future__ import annotations

from unittest.mock import patch

import pytest
from fastapi import HTTPException

from app.core import observability


class TestInitSentry:
    def test_no_op_when_dsn_unset(self):
        with patch.object(observability.settings, "SENTRY_DSN", None):
            assert observability.init_sentry() is False

    def test_no_op_when_dsn_empty(self):
        with patch.object(observability.settings, "SENTRY_DSN", ""):
            assert observability.init_sentry() is False

    def test_initializes_when_dsn_set(self):
        # Use a syntactically-valid but inert test DSN. sentry-sdk accepts
        # any well-formed DSN — actual events would 404 against the
        # fake project but `init()` itself returns successfully.
        fake_dsn = "https://abc@o0.ingest.sentry.io/0"
        with patch.object(observability.settings, "SENTRY_DSN", fake_dsn), \
             patch.object(observability.settings, "SENTRY_ENVIRONMENT", "test"), \
             patch.object(observability.settings, "SENTRY_RELEASE", "deadbeef"), \
             patch("sentry_sdk.init") as mock_init:
            assert observability.init_sentry() is True
            mock_init.assert_called_once()
            kwargs = mock_init.call_args.kwargs
            assert kwargs["dsn"] == fake_dsn
            assert kwargs["environment"] == "test"
            assert kwargs["release"] == "deadbeef"
            assert kwargs["send_default_pii"] is False
            assert callable(kwargs["before_send"])


class TestBeforeSendFilter:
    """The filter decides which events leave the box. We assert:
       - 4xx HTTPExceptions are dropped (return None)
       - 5xx + unhandled exceptions pass through
       - Auth headers + credential body fields get scrubbed
    """

    def _hint(self, exc: Exception) -> dict:
        return {"exc_info": (type(exc), exc, None)}

    def test_drops_401_unauthorized(self):
        result = observability._before_send({}, self._hint(HTTPException(status_code=401)))
        assert result is None

    def test_drops_403_forbidden(self):
        result = observability._before_send({}, self._hint(HTTPException(status_code=403)))
        assert result is None

    def test_drops_404_not_found(self):
        result = observability._before_send({}, self._hint(HTTPException(status_code=404)))
        assert result is None

    def test_drops_422_validation_error(self):
        result = observability._before_send({}, self._hint(HTTPException(status_code=422)))
        assert result is None

    def test_keeps_500_server_error(self):
        result = observability._before_send({"request": {}}, self._hint(HTTPException(status_code=500)))
        assert result is not None

    def test_keeps_unhandled_exception(self):
        result = observability._before_send({"request": {}}, self._hint(ValueError("boom")))
        assert result is not None

    def test_keeps_event_without_hint(self):
        # Performance transactions arrive without exc_info; they should pass.
        result = observability._before_send({"type": "transaction"}, {})
        assert result is not None


class TestScrubbing:
    def test_strips_authorization_header(self):
        event = {"request": {"headers": {"Authorization": "Bearer secret", "X-Other": "ok"}}}
        scrubbed = observability._scrub_event(event)
        assert scrubbed["request"]["headers"]["Authorization"] == "[scrubbed]"
        assert scrubbed["request"]["headers"]["X-Other"] == "ok"

    def test_strips_cookie_headers_case_insensitive(self):
        event = {"request": {"headers": {"cookie": "access_token=x", "Set-Cookie": "y=1"}}}
        scrubbed = observability._scrub_event(event)
        assert scrubbed["request"]["headers"]["cookie"] == "[scrubbed]"
        assert scrubbed["request"]["headers"]["Set-Cookie"] == "[scrubbed]"

    def test_strips_csrf_header(self):
        event = {"request": {"headers": {"X-CSRF-Token": "abc"}}}
        scrubbed = observability._scrub_event(event)
        assert scrubbed["request"]["headers"]["X-CSRF-Token"] == "[scrubbed]"

    def test_strips_password_body_fields(self):
        event = {"request": {"data": {"email": "a@b.test", "password": "hunter2", "new_password": "x"}}}
        scrubbed = observability._scrub_event(event)
        assert scrubbed["request"]["data"]["email"] == "a@b.test"
        assert scrubbed["request"]["data"]["password"] == "[scrubbed]"
        assert scrubbed["request"]["data"]["new_password"] == "[scrubbed]"

    def test_strips_refresh_token_body_field(self):
        event = {"request": {"data": {"refresh_token": "xyz"}}}
        scrubbed = observability._scrub_event(event)
        assert scrubbed["request"]["data"]["refresh_token"] == "[scrubbed]"

    def test_no_op_without_request(self):
        # Events from background tasks have no request dict — scrubber
        # shouldn't blow up.
        scrubbed = observability._scrub_event({"level": "error"})
        assert scrubbed == {"level": "error"}


class TestUserContextHelpers:
    """set/clear_user_context call into sentry_sdk and should be no-ops
    when Sentry isn't initialized — sentry_sdk.set_user is safe against
    a disabled hub. We assert these don't raise."""

    def test_set_user_context_no_op_when_inactive(self):
        # Not initialized in test env — should not raise.
        observability.set_user_context(42, role="admin")

    def test_set_user_context_without_role(self):
        observability.set_user_context(7)

    def test_clear_user_context_no_op_when_inactive(self):
        observability.clear_user_context()
