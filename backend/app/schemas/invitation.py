"""Invitation schemas."""
from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime


class InvitationCreate(BaseModel):
    email: EmailStr
    first_name: str
    last_name: str
    role: str  # 'player' or 'parent'
    team_id: Optional[int] = None


class InvitationResponse(BaseModel):
    id: int
    email: str
    first_name: str
    last_name: str
    role: str
    team_id: Optional[int]
    team_name: Optional[str]
    status: str
    expires_at: datetime
    created_at: datetime
    
    class Config:
        from_attributes = True


class InvitationListResponse(BaseModel):
    items: list[InvitationResponse]
    total: int


class InvitationAcceptRequest(BaseModel):
    token: str
    

class InvitationVerifyResponse(BaseModel):
    valid: bool
    email: Optional[str] = None
    role: Optional[str] = None
    team_id: Optional[int] = None
    team_name: Optional[str] = None
    message: Optional[str] = None
