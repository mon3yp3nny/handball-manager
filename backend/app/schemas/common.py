"""Common pagination schemas."""
from pydantic import BaseModel, Field
from typing import List, Generic, TypeVar, Optional
from datetime import datetime


T = TypeVar('T')


class PaginationParams(BaseModel):
    """Query parameters for pagination."""
    skip: int = Field(0, ge=0)
    limit: int = Field(100, ge=1, le=1000)


class PaginatedResponse(BaseModel, Generic[T]):
    """Base paginated response model."""
    items: List[T]
    total: int
    skip: int
    limit: int
    
    class Config:
        from_attributes = True


class DashboardStats(BaseModel):
    """Dashboard statistics response."""
    total_teams: int
    total_players: int
    total_games: int
    total_events: int
    upcoming_games: int
    upcoming_events: int


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    version: str
    timestamp: Optional[datetime] = None
