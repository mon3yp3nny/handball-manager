from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime, date
from enum import Enum


class Position(str, Enum):
    GOALKEEPER = "goalkeeper"
    LEFT_WING = "left_wing"
    LEFT_BACK = "left_back"
    CENTER_BACK = "center_back"
    RIGHT_BACK = "right_back"
    RIGHT_WING = "right_wing"
    PIVOT = "pivot"
    DEFENSE = "defense"


# Base schemas
class PlayerBase(BaseModel):
    jersey_number: Optional[int] = Field(None, ge=1, le=99)
    position: Optional[Position] = None
    date_of_birth: Optional[date] = None
    emergency_contact_name: Optional[str] = Field(None, max_length=200)
    emergency_contact_phone: Optional[str] = Field(
        None, max_length=30, pattern=r"^\+?[\d\s\-()]{6,30}$"
    )


# Create schemas
class PlayerCreate(PlayerBase):
    user_id: int
    team_id: Optional[int] = None
    parent_ids: Optional[List[int]] = None  # IDs of parents to link
    create_parents: Optional[List[dict]] = None  # Create new parent users


# Update schemas
class PlayerUpdate(BaseModel):
    jersey_number: Optional[int] = Field(None, ge=1, le=99)
    position: Optional[Position] = None
    date_of_birth: Optional[date] = None
    emergency_contact_name: Optional[str] = Field(None, max_length=200)
    emergency_contact_phone: Optional[str] = Field(
        None, max_length=30, pattern=r"^\+?[\d\s\-()]{6,30}$"
    )
    team_id: Optional[int] = None


# Response schemas
class PlayerResponse(PlayerBase):
    id: int
    user_id: int
    team_id: Optional[int]
    games_played: int
    goals_scored: int
    assists: int
    created_at: datetime
    updated_at: datetime
    user: Optional["UserBase"] = None

    class Config:
        from_attributes = True


class ParentInfo(BaseModel):
    id: int
    email: str
    first_name: str
    last_name: str
    phone: Optional[str] = None


class PlayerWithStats(PlayerResponse):
    team_name: Optional[str] = None
    parents: List[ParentInfo] = []

    class Config:
        from_attributes = True


# Import for circular reference
from app.schemas.user import UserBase
PlayerResponse.model_rebuild()
PlayerWithStats.model_rebuild()
