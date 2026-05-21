"""Sentry wiring (#64).

Behaviour by DSN:
  - empty / unset  → `init_sentry()` is a true no-op; no SDK import side
    effects, no network activity, no perf cost. Dev environments and
    the pytest suite never need to set anything.
  - set            → backend exceptions + slow-request traces ship with
    request context, the deploy's git SHA as the release tag, and
    user_id + role attached to scope when an authenticated request
    hits an endpoint.

What's filtered out before send:
  - Expected HTTPExceptions (4xx) — Sentry isn't an audit log for "user
    typed wrong password". 5xx + unhandled exceptions only.
  - `Authorization` / `Cookie` / `Set-Cookie` headers — we use httpOnly
    cookies for auth and don't want those mirrored into the issue.
  - The `password` / `current_password` / `new_password` body fields,
    if Sentry's HTTP integration captures the request body at all.

What's NOT attached (PII minimization):
  - email, first_name, last_name, IP address. We attach `user_id` and
    `role` only — enough to correlate an error to a user-shaped session
    without exporting member identities to a third-party service.
"""
from __future__ import annotations

import logging
from typing import Any, Optional

from app.core.config import settings

logger = logging.getLogger(__name__)

# Field names whose values we always wipe from event payloads.
_SCRUB_HEADERS = {"authorization", "cookie", "set-cookie", "x-csrf-token"}
_SCRUB_BODY_KEYS = {"password", "current_password", "new_password", "token", "refresh_token"}


def _scrub_event(event: dict[str, Any]) -> dict[str, Any]:
    """Strip auth/credentials from the event before it leaves the box.

    Events from background tasks have no `request` dict — leave the
    event shape untouched in that case so the scrubber is a true no-op.
    """
    request = event.get("request")
    if not isinstance(request, dict):
        return event

    headers = request.get("headers")
    if isinstance(headers, dict):
        for k in list(headers.keys()):
            if k.lower() in _SCRUB_HEADERS:
                headers[k] = "[scrubbed]"

    # Sentry's FastAPI integration doesn't capture the body by default,
    # but we defensively scrub anyway for the case where someone enables
    # `send_default_pii=True` later.
    data = request.get("data")
    if isinstance(data, dict):
        for k in list(data.keys()):
            if k.lower() in _SCRUB_BODY_KEYS:
                data[k] = "[scrubbed]"

    return event


def _before_send(event: dict[str, Any], hint: dict[str, Any]) -> Optional[dict[str, Any]]:
    """Sentry callback: filter expected errors, scrub secrets.

    `hint["exc_info"]` is the live (type, value, tb) tuple — we use the
    type to decide whether the exception is one we actually want to see.
    """
    exc_info = hint.get("exc_info") if hint else None
    if exc_info:
        _, exc, _ = exc_info
        try:
            from fastapi import HTTPException
            from starlette.exceptions import HTTPException as StarletteHTTPException
        except Exception:  # pragma: no cover — FastAPI is always present in this app
            HTTPException = None  # type: ignore[assignment]
            StarletteHTTPException = None  # type: ignore[assignment]

        # 4xx HTTPExceptions are business-as-usual (401 unauth, 404 not
        # found, 422 validation). Only ship 5xx + unhandled exceptions.
        for exc_type in (HTTPException, StarletteHTTPException):
            if exc_type and isinstance(exc, exc_type):
                status = getattr(exc, "status_code", 500)
                if 400 <= status < 500:
                    return None

    return _scrub_event(event)


def init_sentry() -> bool:
    """Initialize Sentry if SENTRY_DSN is configured. Returns True iff init ran.

    Safe to call at any startup point; no-op when DSN is empty. Importing
    sentry-sdk costs ~50ms cold; we still do the import unconditionally
    so the module's other helpers (`set_user_context` etc.) work the
    same whether init ran or not — they're cheap no-ops when no Hub is
    bound.
    """
    dsn = getattr(settings, "SENTRY_DSN", None)
    if not dsn:
        logger.info("Sentry DSN not set — error monitoring disabled.")
        return False

    try:
        import sentry_sdk
        from sentry_sdk.integrations.fastapi import FastApiIntegration
        from sentry_sdk.integrations.starlette import StarletteIntegration
        from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
    except ImportError:
        logger.warning(
            "SENTRY_DSN is set but sentry-sdk is not installed. "
            "Run `pip install -r requirements.txt`."
        )
        return False

    sentry_sdk.init(
        dsn=dsn,
        environment=getattr(settings, "SENTRY_ENVIRONMENT", "production"),
        release=getattr(settings, "SENTRY_RELEASE", None) or None,
        traces_sample_rate=getattr(settings, "SENTRY_TRACES_SAMPLE_RATE", 0.1),
        # Don't send PII (no IPs, no usernames). We attach user_id+role
        # ourselves via set_user_context.
        send_default_pii=False,
        before_send=_before_send,
        integrations=[
            StarletteIntegration(),
            FastApiIntegration(),
            SqlalchemyIntegration(),
        ],
    )
    logger.info(
        "Sentry initialized (environment=%s, release=%s, sample_rate=%s).",
        getattr(settings, "SENTRY_ENVIRONMENT", "production"),
        getattr(settings, "SENTRY_RELEASE", None) or "<unset>",
        getattr(settings, "SENTRY_TRACES_SAMPLE_RATE", 0.1),
    )
    return True


def set_user_context(user_id: int | str, role: Optional[str] = None) -> None:
    """Attach the authenticated user's id + role to the current scope.

    Called by `get_current_user`. No-op when Sentry isn't initialized
    (sentry_sdk.set_user is safe to call against a disabled hub).
    """
    try:
        import sentry_sdk
    except ImportError:
        return
    sentry_sdk.set_user({"id": str(user_id), "role": role} if role else {"id": str(user_id)})


def clear_user_context() -> None:
    """Drop user context from the current scope (called on logout)."""
    try:
        import sentry_sdk
    except ImportError:
        return
    sentry_sdk.set_user(None)
