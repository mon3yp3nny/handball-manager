"""Common pagination schemas."""
from typing import List, Generic, TypeVar, Optional
from datetime import datetime

from pydantic import BaseModel, Field, computed_field


T = TypeVar('T')


class PaginationParams(BaseModel):
    """Query parameters for pagination."""
    skip: int = Field(0, ge=0)
    limit: int = Field(100, ge=1, le=1000)


class PaginatedResponse(BaseModel, Generic[T]):
    """Paginated list response with derived navigation metadata (#105).

    The four primitive fields (`items` / `total` / `skip` / `limit`) come
    straight from the query; the three computed ones (`page` / `pages` /
    `has_more`) are derived so the client never has to recompute and
    page-vs-skip semantics stay consistent across endpoints.
    """
    items: List[T]
    total: int
    skip: int
    limit: int

    @computed_field  # type: ignore[misc]
    @property
    def page(self) -> int:
        """1-based current page number (skip // limit + 1, min 1)."""
        if self.limit <= 0:
            return 1
        return (self.skip // self.limit) + 1

    @computed_field  # type: ignore[misc]
    @property
    def pages(self) -> int:
        """Total page count for the current limit (min 1 even when empty)."""
        if self.limit <= 0 or self.total == 0:
            return 1
        return (self.total + self.limit - 1) // self.limit

    @computed_field  # type: ignore[misc]
    @property
    def has_more(self) -> bool:
        """True if more rows exist past `skip + limit` — saves a follow-up
        HEAD/count call when the client just needs 'show More' logic."""
        return self.skip + self.limit < self.total

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
