from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


# Base schemas
class TeamBase(BaseModel):
    name: str
    description: Optional[str] = None
    age_group: Optional[str] = None


# Create schemas
class TeamCreate(TeamBase):
    coach_id: Optional[int] = None


# Update schemas
class TeamUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    age_group: Optional[str] = None
    coach_id: Optional[int] = None


# Response schemas
class TeamResponse(TeamBase):
    id: int
    coach_id: Optional[int]
    created_at: datetime
    updated_at: datetime
    player_count: Optional[int] = 0
    
    class Config:
        from_attributes = True


class TeamWithPlayers(TeamResponse):
    players: List["PlayerResponse"] = []
    
    class Config:
        from_attributes = True


# Import for circular reference
from app.schemas.player import PlayerResponse
TeamWithPlayers.model_rebuild()
