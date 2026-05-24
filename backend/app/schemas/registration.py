"""Schemas for the registration approval workflow."""
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field

from app.schemas.user import UserRole


class PendingRegistration(BaseModel):
    """A user awaiting approval, as shown in an approver's queue."""
    id: int
    email: str
    first_name: str
    last_name: str
    role: UserRole
    roles: List[UserRole] = []
    requested_team_id: Optional[int] = None
    requested_team_name: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class RejectionRequest(BaseModel):
    reason: str = Field(..., min_length=1, max_length=500)


class PublicTeam(BaseModel):
    """Minimal team info for the public sign-up team picker (no auth)."""
    id: int
    name: str
    age_group: Optional[str] = None

    class Config:
        from_attributes = True


class MyTeams(BaseModel):
    """The current user's teams, split for the team-scoped sidebar:
    `managed` = teams they coach; `member` = their own team plus any
    team a child of theirs plays in."""
    managed: List[PublicTeam] = []
    member: List[PublicTeam] = []
