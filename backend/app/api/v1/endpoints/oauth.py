"""OAuth authentication endpoints."""
import logging
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Response, status, Request
from sqlalchemy.orm import Session
from typing import Optional

from app.db.session import get_db
from app.core import security
from app.core.deps import get_current_user
from app.core.rate_limit import limiter
from app.models.team import Team
from app.models.player import Player
from app.services.approval import notify_approvers_of_registration
from app.websocket.manager import notify_resource
from app.services.oauth_service import (
    verify_google_token,
    verify_apple_token,
    oauth_service
)
from app.schemas.oauth import OAuthLoginRequest, OAuthCallbackResponse, OAuthRoleSelection
from app.models.user import User, UserRole, ApprovalStatus
from app.core.config import settings

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/google", response_model=OAuthCallbackResponse)
@limiter.limit("10/minute")
async def google_oauth_login(
    request: Request,
    response: Response,
    oauth_request: OAuthLoginRequest,
    db: Session = Depends(get_db),
):
    """
    Login with Google OAuth token.
    Frontend receives token from Google Sign In button and sends it here.
    """
    if oauth_request.provider != "google":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Provider must be 'google'"
        )

    # Verify the Google token
    oauth_info = verify_google_token(oauth_request.token)
    if not oauth_info:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Google token"
        )

    # Get or create user
    user, is_new_user = oauth_service.get_or_create_user(db, oauth_info)

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is disabled"
        )

    logger.info("Google OAuth login: user_id=%s, is_new=%s", user.id, is_new_user)

    # Create tokens + set cookies (#42).
    tokens = oauth_service.create_tokens(user)
    csrf = security.set_auth_cookies(response, tokens["access_token"], tokens["refresh_token"])
    response.headers["X-CSRF-Token"] = csrf

    return OAuthCallbackResponse(
        access_token=tokens["access_token"],
        refresh_token=tokens["refresh_token"],
        token_type="bearer",
        user_id=user.id,
        email=user.email,
        role=user.role.value,
        first_name=user.first_name,
        last_name=user.last_name,
        is_new_user=is_new_user,
        needs_role_selection=not user.role_selected,
    )


@router.post("/apple", response_model=OAuthCallbackResponse)
@limiter.limit("10/minute")
async def apple_oauth_login(
    request: Request,
    response: Response,
    oauth_request: OAuthLoginRequest,
    db: Session = Depends(get_db),
):
    """
    Login with Apple OAuth token.
    Frontend receives token from Apple Sign In button and sends it here.

    Note: Apple only provides first_name and last_name on the first login.
    Frontend should store these and send them if user is new.
    """
    if oauth_request.provider != "apple":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Provider must be 'apple'"
        )

    # Verify the Apple token
    oauth_info = verify_apple_token(oauth_request.token)
    if not oauth_info:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Apple token"
        )

    # Use first_name/last_name from request if provided (for new Apple users)
    if oauth_request.first_name:
        oauth_info.first_name = oauth_request.first_name
    if oauth_request.last_name:
        oauth_info.last_name = oauth_request.last_name

    # Get or create user
    user, is_new_user = oauth_service.get_or_create_user(db, oauth_info)

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is disabled"
        )

    logger.info("Apple OAuth login: user_id=%s, is_new=%s", user.id, is_new_user)

    # Create tokens + set cookies (#42).
    tokens = oauth_service.create_tokens(user)
    csrf = security.set_auth_cookies(response, tokens["access_token"], tokens["refresh_token"])
    response.headers["X-CSRF-Token"] = csrf

    return OAuthCallbackResponse(
        access_token=tokens["access_token"],
        refresh_token=tokens["refresh_token"],
        token_type="bearer",
        user_id=user.id,
        email=user.email,
        role=user.role.value,
        first_name=user.first_name,
        last_name=user.last_name,
        is_new_user=is_new_user,
        needs_role_selection=not user.role_selected,
    )


@router.post("/set-role")
async def set_oauth_user_role(
    selection: OAuthRoleSelection,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Set role for OAuth user during the initial registration flow.

    Idempotent guard (#88): once a user has chosen a role, this endpoint
    refuses further changes — preventing self-service privilege escalation.

    Approval parity: like password registration, choosing a non-admin role
    drops the OAuth user into PENDING approval (coach/supervisor → admin;
    player/parent → the chosen team's coach, admin fallback). The user is
    still APPROVED at the moment they reach here — they were created
    approved and haven't picked a role yet — so the approval gate doesn't
    block this call.
    """
    if not current_user.is_oauth_only:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only OAuth users can set role this way",
        )

    role = selection.role

    if current_user.role_selected:
        logger.warning(
            "Blocked /oauth/set-role re-call by user_id=%s (already chose %s, requested %s)",
            current_user.id, current_user.role.value, role.value,
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Role has already been selected and cannot be changed via this endpoint",
        )

    if role == UserRole.ADMIN:
        logger.warning(
            "Blocked self-service ADMIN role selection by user_id=%s", current_user.id,
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin role cannot be self-assigned",
        )

    # Player/parent must pick a team so approval routes to its coach.
    requested_team: Optional[Team] = None
    if role in (UserRole.PLAYER, UserRole.PARENT):
        if not selection.requested_team_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Please select a team to register as a player or parent.",
            )
        requested_team = db.query(Team).filter(
            Team.id == selection.requested_team_id
        ).first()
        if not requested_team:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Selected team does not exist.",
            )

    current_user.role = role
    current_user.role_selected = True
    current_user.approval_status = ApprovalStatus.PENDING
    current_user.requested_team_id = requested_team.id if requested_team else None
    # Mirror the password flow: a player gets a Player profile, unattached
    # until approval. (OAuth users previously never got one.)
    if role == UserRole.PLAYER:
        existing = db.query(Player).filter(Player.user_id == current_user.id).first()
        if not existing:
            db.add(Player(user_id=current_user.id))
    db.commit()
    db.refresh(current_user)

    logger.info("OAuth user user_id=%s set role to %s (pending approval)",
                current_user.id, role.value)
    notify_approvers_of_registration(db, current_user, requested_team, background_tasks)
    notify_resource("registrations", "created")

    return {
        "message": "Role saved. Your account is awaiting approval.",
        "role": role.value,
        "approval_status": current_user.approval_status.value,
    }
