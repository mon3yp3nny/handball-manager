from pydantic import BaseModel
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
    opponent: str
    location: str
    scheduled_at: datetime
    game_type: GameType = GameType.LEAGUE
    is_home_game: bool = True
    notes: Optional[str] = None


# Create schemas
class GameCreate(GameBase):
    team_id: int


# Update schemas
class GameUpdate(BaseModel):
    opponent: Optional[str] = None
    location: Optional[str] = None
    scheduled_at: Optional[datetime] = None
    game_type: Optional[GameType] = None
    status: Optional[GameStatus] = None
    home_score: Optional[int] = None
    away_score: Optional[int] = None
    is_home_game: Optional[bool] = None
    notes: Optional[str] = None


class GameResultUpdate(BaseModel):
    home_score: int
    away_score: int
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
