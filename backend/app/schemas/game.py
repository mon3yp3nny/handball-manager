from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum


class GameStatus(str, Enum):
    SCHEDULED = "scheduled"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class GameType(str, Enum):
    LEAGUE = "league"
    TOURNAMENT = "tournament"
    FRIENDLY = "friendly"
    CUP = "cup"


# Base schemas
class GameBase(BaseModel):
    opponent: str = Field(..., min_length=1, max_length=200)
    location: str = Field(..., min_length=1, max_length=300)
    scheduled_at: datetime
    game_type: GameType = GameType.LEAGUE
    is_home_game: bool = True
    notes: Optional[str] = Field(None, max_length=2000)


# Create schemas
class GameCreate(GameBase):
    team_id: int


# Update schemas
class GameUpdate(BaseModel):
    opponent: Optional[str] = Field(None, min_length=1, max_length=200)
    location: Optional[str] = Field(None, min_length=1, max_length=300)
    scheduled_at: Optional[datetime] = None
    game_type: Optional[GameType] = None
    status: Optional[GameStatus] = None
    home_score: Optional[int] = Field(None, ge=0)
    away_score: Optional[int] = Field(None, ge=0)
    is_home_game: Optional[bool] = None
    notes: Optional[str] = Field(None, max_length=2000)


class GameResultUpdate(BaseModel):
    home_score: int = Field(..., ge=0)
    away_score: int = Field(..., ge=0)
    status: GameStatus = GameStatus.COMPLETED


# Response schemas
class GameResponse(GameBase):
    id: int
    team_id: int
    status: GameStatus
    home_score: Optional[int]
    away_score: Optional[int]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class GameWithTeam(GameResponse):
    team_name: Optional[str] = None

    class Config:
        from_attributes = True
