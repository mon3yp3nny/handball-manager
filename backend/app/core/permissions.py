"""Reusable role-based authorization dependencies."""
from fastapi import Depends, HTTPException, status
from app.core.deps import get_current_user
from app.models.user import User, UserRole


def require_roles(*roles: UserRole):
    """FastAPI dependency that restricts access to the given roles.

    Usage::

        @router.get("/admin-only")
        def admin_view(user: User = Depends(require_roles(UserRole.ADMIN))):
            ...
    """
    allowed = set(roles)

    def _checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in allowed:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required roles: {[r.value for r in allowed]}",
            )
        return current_user

    return _checker
