from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from typing import Optional

from app.db.session import get_db
from app.core.config import settings
from app.core.security import decode_token
from app.models.user import User, UserRole

# OAuth2 scheme stays — kept as the documented Bearer mechanism for
# API clients (E2E suite, future mobile, curl). The cookie path below
# is preferred when both are present.
# auto_error=False so requests without a header don't 401 here; the
# cookie path below gets a chance first.
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=False)


def get_current_user(
    request: Request,
    token: Optional[str] = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    """Resolve the caller to a User. Token sources (in order):

    1. ``access_token`` httpOnly cookie — the default for browser SPAs
       after #42 moved tokens out of localStorage.
    2. ``Authorization: Bearer <token>`` header — kept as a fallback
       so API clients (E2E suite, curl, future mobile apps) keep working.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    # Cookie takes precedence — see docstring.
    cookie_token = request.cookies.get(settings.AUTH_COOKIE_NAME_ACCESS)
    presented = cookie_token or token
    if not presented:
        raise credentials_exception

    payload = decode_token(presented)
    if payload is None or payload.get("type") != "access":
        raise credentials_exception

    email: Optional[str] = payload.get("sub")
    if email is None:
        raise credentials_exception

    user = db.query(User).filter(User.email == email).first()
    if user is None or not user.is_active:
        raise credentials_exception

    # Attach user_id + role to the Sentry scope so any downstream
    # exception captured during this request carries identity. No-op
    # when Sentry isn't initialized. PII-minimal: id + role only,
    # never email/name/IP. See #64.
    from app.core.observability import set_user_context
    set_user_context(user.id, role=user.role.value if user.role else None)

    return user


def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    return current_user


def require_role(roles: list[UserRole]):
    """Require user to have ANY of the specified roles."""
    def role_checker(current_user: User = Depends(get_current_user)):
        # Check if user has any of the required roles
        if not current_user.has_any_role(roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required roles: {[r.value for r in roles]}"
            )
        return current_user
    return role_checker


def require_all_roles(roles: list[UserRole]):
    """Require user to have ALL of the specified roles."""
    def role_checker(current_user: User = Depends(get_current_user)):
        if not current_user.has_all_roles(roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required all roles: {[r.value for r in roles]}"
            )
        return current_user
    return role_checker


# Role-specific dependencies
require_admin = require_role([UserRole.ADMIN])
require_coach = require_role([UserRole.COACH, UserRole.ADMIN])
require_coach_or_supervisor = require_role([UserRole.COACH, UserRole.SUPERVISOR, UserRole.ADMIN])
require_player = require_role([UserRole.PLAYER, UserRole.COACH, UserRole.SUPERVISOR, UserRole.ADMIN])
require_parent = require_role([UserRole.PARENT, UserRole.ADMIN])
