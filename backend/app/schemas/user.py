from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional, List
from datetime import datetime
from enum import Enum


class UserRole(str, Enum):
    ADMIN = "admin"
    COACH = "coach"
    SUPERVISOR = "supervisor"
    PLAYER = "player"
    PARENT = "parent"


# Base schemas
class UserBase(BaseModel):
    email: EmailStr
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    phone: Optional[str] = Field(None, max_length=30, pattern=r"^\+?[\d\s\-()]{6,30}$")
    role: UserRole = UserRole.PLAYER


# Create schemas
class UserCreate(UserBase):
    password: str = Field(..., min_length=8, max_length=128)


# Update schemas
class UserUpdate(BaseModel):
    first_name: Optional[str] = Field(None, min_length=1, max_length=100)
    last_name: Optional[str] = Field(None, min_length=1, max_length=100)
    phone: Optional[str] = Field(None, max_length=30, pattern=r"^\+?[\d\s\-()]{6,30}$")
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None


# Response schemas
class UserResponse(UserBase):
    id: int
    is_active: bool
    is_verified: bool
    roles: List[UserRole] = []
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class UserInDB(UserBase):
    """User as stored in database (includes hashed password)."""
    id: int
    hashed_password: Optional[str] = None
    is_active: bool = True
    is_verified: bool = False
    is_oauth_only: bool = False
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    role: UserRole


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class PasswordReset(BaseModel):
    token: str
    new_password: str = Field(..., min_length=8, max_length=128)


class PasswordChange(BaseModel):
    old_password: str
    new_password: str = Field(..., min_length=8, max_length=128)


class InvitationCreate(BaseModel):
    email: EmailStr
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    role: UserRole
    team_id: Optional[int] = None


class UserRoleUpdate(BaseModel):
    """Schema for updating user role."""
    role: UserRole


class AdminUserCreate(UserBase):
    """Admin creating user - password optional (can be set later)."""
    password: Optional[str] = Field(None, min_length=8, max_length=128)
    is_active: bool = True
    is_verified: bool = True


class UserActivityResponse(BaseModel):
    id: int
    activity_type: str
    description: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class UserStats(BaseModel):
    total_users: int
    active_users: int
    inactive_users: int
    users_by_role: dict
    recent_activity_7d: int
