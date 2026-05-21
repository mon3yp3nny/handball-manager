"""CSRF protection via double-submit cookie (#42).

For browser-cookie auth, the threat is that a malicious site forces the
user's browser to issue a state-changing request to our backend; the
browser auto-attaches the auth cookies and the call succeeds.

Mitigation: on login we set a ``csrf_token`` cookie that is NOT
httpOnly. The SPA reads that cookie, echoes its value back as the
``X-CSRF-Token`` header on every state-changing request. The middleware
below double-submits: it only accepts the request if the cookie and the
header are present and equal.

Bypass conditions — kept narrow on purpose:
- Safe methods (GET / HEAD / OPTIONS) — no state change, no CSRF risk.
- Login / register / forgot-password — pre-auth, no cookie yet.
- Requests authenticated via the ``Authorization`` header — API clients
  bypass cookies entirely, so cross-origin CSRF doesn't apply (the
  attacker would also need the bearer token, which we don't grant to
  arbitrary origins).

Anything else with a cookie but no matching CSRF header → 403.
"""
from typing import Iterable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from app.core.config import settings


# Endpoints that must remain reachable without a CSRF token — they're
# the ones that *establish* the session in the first place.
_OPEN_PATHS: tuple[str, ...] = (
    "/api/v1/auth/login",
    "/api/v1/auth/login/",
    "/api/v1/auth/register",
    "/api/v1/auth/forgot-password",
    "/api/v1/auth/refresh",  # the cookie is the refresh; treat like login
    "/api/v1/oauth/google",
    "/api/v1/oauth/apple",
    "/api/v1/oauth/set-role",
)

_SAFE_METHODS: frozenset[str] = frozenset({"GET", "HEAD", "OPTIONS"})


class CSRFMiddleware(BaseHTTPMiddleware):
    """Enforce X-CSRF-Token on cookie-authenticated writes."""

    async def dispatch(self, request: Request, call_next):
        if request.method in _SAFE_METHODS:
            return await call_next(request)
        if request.url.path in _OPEN_PATHS:
            return await call_next(request)

        # No auth cookie → either pre-auth or bearer-only; let it through
        # (the actual endpoint will 401 if auth is required).
        cookie = request.cookies.get(settings.AUTH_COOKIE_NAME_ACCESS)
        if not cookie:
            return await call_next(request)

        # We have an auth cookie. Require the matching CSRF token.
        csrf_cookie = request.cookies.get(settings.AUTH_COOKIE_NAME_CSRF)
        csrf_header = request.headers.get("X-CSRF-Token")
        if not csrf_cookie or not csrf_header or csrf_cookie != csrf_header:
            return JSONResponse(
                {"detail": "CSRF token missing or mismatched"},
                status_code=403,
            )
        return await call_next(request)
