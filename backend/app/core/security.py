from datetime import datetime, timedelta
from app.utils.time import utcnow
from typing import Optional, Union

# PyJWT (the maintained, modern JOSE-token library). python-jose was
# removed in #85 — both libraries expose the same `jwt.encode` /
# `jwt.decode` API for HS256, so the only swap was the exception type:
# jose.JWTError → jwt.PyJWTError (covers ExpiredSignatureError,
# InvalidTokenError, and friends). `oauth_service.py` was already using
# this library; consolidating here cuts a duplicated dep + a known
# CVE-history dependency.
import jwt

from passlib.context import CryptContext
from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = utcnow() + expires_delta
    else:
        expire = utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire, "type": "access"})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def create_refresh_token(data: dict) -> str:
    to_encode = data.copy()
    expire = utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def decode_token(token: str) -> Optional[dict]:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except jwt.PyJWTError:
        return None


# ----- Cookie-auth helpers (#42) ------------------------------------------
#
# Tokens are sent as httpOnly cookies so XSS can't read them out of
# `document.cookie` / localStorage. A separate CSRF token cookie (NOT
# httpOnly) accompanies them — the frontend reads that one and echoes it
# back as an `X-CSRF-Token` header on state-changing requests. The
# middleware in `core/csrf.py` then double-submits the cookie vs the
# header.
#
# Bearer tokens still work via the Authorization header — kept as a
# fallback for API clients (E2E suite, future mobile apps, curl scripts).
# get_current_user prefers the cookie when both are present.

import secrets as _secrets

from fastapi import Response


def _cookie_kwargs(max_age: int) -> dict:
    """Common kwargs for setting auth cookies. Centralized so SameSite /
    Secure / Domain stay consistent across access, refresh, and CSRF."""
    return {
        "max_age": max_age,
        "samesite": settings.AUTH_COOKIE_SAMESITE,
        "secure": settings.AUTH_COOKIE_SECURE,
        "domain": settings.AUTH_COOKIE_DOMAIN,
        "path": "/",
    }


def set_auth_cookies(response: Response, access_token: str, refresh_token: str) -> str:
    """Attach access + refresh + CSRF cookies to ``response``.

    Returns the CSRF token so the caller can also include it in the
    JSON body (helps SPAs grab it without parsing cookies, and supports
    bootstrapping the very first request after login).
    """
    access_max = settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    refresh_max = settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60

    response.set_cookie(
        settings.AUTH_COOKIE_NAME_ACCESS,
        access_token,
        httponly=True,
        **_cookie_kwargs(access_max),
    )
    response.set_cookie(
        settings.AUTH_COOKIE_NAME_REFRESH,
        refresh_token,
        httponly=True,
        **_cookie_kwargs(refresh_max),
    )
    csrf_token = _secrets.token_urlsafe(32)
    response.set_cookie(
        settings.AUTH_COOKIE_NAME_CSRF,
        csrf_token,
        httponly=False,  # frontend must read this and echo as X-CSRF-Token
        **_cookie_kwargs(refresh_max),
    )
    return csrf_token


def clear_auth_cookies(response: Response) -> None:
    """Wipe all three auth cookies — called from /auth/logout. We
    explicitly set max_age=0 + empty value rather than relying on
    `response.delete_cookie` so the domain/path/samesite/secure
    attributes match the original set_cookie call (browsers only
    delete cookies whose attributes match)."""
    for name in (
        settings.AUTH_COOKIE_NAME_ACCESS,
        settings.AUTH_COOKIE_NAME_REFRESH,
        settings.AUTH_COOKIE_NAME_CSRF,
    ):
        response.set_cookie(
            name,
            "",
            httponly=(name != settings.AUTH_COOKIE_NAME_CSRF),
            **_cookie_kwargs(0),
        )
