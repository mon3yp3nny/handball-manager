from pydantic import BaseModel
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
    jersey_number: Optional[int] = None
    position: Optional[Position] = None
    date_of_birth: Optional[date] = None
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None


# Create schemas
class PlayerCreate(PlayerBase):
    user_id: int
    team_id: Optional[int] = None


# Update schemas
class PlayerUpdate(BaseModel):
    jersey_number: Optional[int] = None
    position: Optional[Position] = None
    date_of_birth: Optional[date] = None
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None
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


class PlayerWithStats(PlayerResponse):
    team_name: Optional[str] = None
    
    class Config:
        from_attributes = True


# Import for circular reference
from app.schemas.user import UserBase
PlayerResponse.model_rebuild()
