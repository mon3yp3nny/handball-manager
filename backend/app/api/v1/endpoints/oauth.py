"""OAuth authentication endpoints."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional

from app.db.session import get_db
from app.core.deps import get_current_user
from app.services.oauth_service import (
    verify_google_token, 
    verify_apple_token,
    oauth_service
)
from app.schemas.oauth import OAuthLoginRequest, OAuthCallbackResponse
from app.schemas.token import Token
from app.models.user import User, UserRole
from app.core.config import settings

router = APIRouter()


@router.post("/google", response_model=OAuthCallbackResponse)
async def google_oauth_login(
    request: OAuthLoginRequest,
    db: Session = Depends(get_db)
):
    """
    Login with Google OAuth token.
    Frontend receives token from Google Sign In button and sends it here.
    """
    if request.provider != "google":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Provider must be 'google'"
        )
    
    # Verify the Google token
    oauth_info = verify_google_token(request.token)
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
    
    # Create tokens
    tokens = oauth_service.create_tokens(user)
    
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
        needs_role_selection=is_new_user  # New users need to select role
    )


@router.post("/apple", response_model=OAuthCallbackResponse)
async def apple_oauth_login(
    request: OAuthLoginRequest,
    db: Session = Depends(get_db)
):
    """
    Login with Apple OAuth token.
    Frontend receives token from Apple Sign In button and sends it here.
    
    Note: Apple only provides first_name and last_name on the first login.
    Frontend should store these and send them if user is new.
    """
    if request.provider != "apple":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Provider must be 'apple'"
        )
    
    # Verify the Apple token
    oauth_info = verify_apple_token(request.token)
    if not oauth_info:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Apple token"
        )
    
    # Use first_name/last_name from request if provided (for new Apple users)
    if request.first_name:
        oauth_info.first_name = request.first_name
    if request.last_name:
        oauth_info.last_name = request.last_name
    
    # Get or create user
    user, is_new_user = oauth_service.get_or_create_user(db, oauth_info)
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is disabled"
        )
    
    # Create tokens
    tokens = oauth_service.create_tokens(user)
    
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
        needs_role_selection=is_new_user  # New users need to select role
    )


@router.post("/set-role")
async def set_oauth_user_role(
    role: UserRole,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Set role for OAuth user (called after first login if needs_role_selection is true).
    """
    if not current_user.is_oauth_only:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only OAuth users can set role this way"
        )
    
    current_user.role = role
    db.commit()
    
    return {"message": "Role updated successfully", "role": role.value}
