from pydantic import BaseModel, EmailStr, Field
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
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class UserInDB(UserBase):
    id: int
    hashed_password: str
    is_active: bool

    class Config:
        from_attributes = True


# Login
class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    email: Optional[str] = None
    role: Optional[UserRole] = None
