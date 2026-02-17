"""Invitation schemas."""
from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime


class InvitationCreate(BaseModel):
    email: EmailStr
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    role: str = Field(..., pattern=r"^(player|parent)$")  # 'player' or 'parent'
    team_id: Optional[int] = None


class InvitationResponse(BaseModel):
    id: int
    email: str
    first_name: str
    last_name: str
    role: str
    team_id: Optional[int] = None
    team_name: Optional[str] = None
    status: str
    expires_at: datetime
    created_at: datetime

    class Config:
        from_attributes = True


class InvitationListResponse(BaseModel):
    items: list[InvitationResponse]
    total: int


class InvitationAcceptRequest(BaseModel):
    token: str = Field(..., min_length=1, max_length=200)


class InvitationVerifyResponse(BaseModel):
    valid: bool
    email: Optional[str] = None
    role: Optional[str] = None
    team_id: Optional[int] = None
    team_name: Optional[str] = None
    message: Optional[str] = None
