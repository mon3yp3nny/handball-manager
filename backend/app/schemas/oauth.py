"""Schemas for OAuth authentication."""
from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime


class OAuthLoginRequest(BaseModel):
    """Request to login via OAuth token from frontend."""
    token: str
    provider: str  # 'google' or 'apple'
    first_name: Optional[str] = None  # For Apple first-time login
    last_name: Optional[str] = None   # For Apple first-time login


class OAuthUserInfo(BaseModel):
    """User info extracted from OAuth provider."""
    email: EmailStr
    provider: str
    provider_account_id: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    picture: Optional[str] = None
    is_verified_email: bool = True


class OAuthAccountResponse(BaseModel):
    """Response model for OAuth account."""
    id: int
    provider: str
    provider_email: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True


class OAuthCallbackResponse(BaseModel):
    """Response after OAuth callback."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user_id: int
    email: str
    role: str
    first_name: str
    last_name: str
    is_new_user: bool = False
    needs_role_selection: bool = False
