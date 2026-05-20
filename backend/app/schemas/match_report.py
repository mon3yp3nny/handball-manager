"""Schemas for match reports (#131)."""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class MatchReportBase(BaseModel):
    body: str = Field(..., min_length=1, max_length=10_000)
    man_of_the_match_player_id: Optional[int] = None


class MatchReportCreate(MatchReportBase):
    pass


class MatchReportUpdate(BaseModel):
    body: Optional[str] = Field(None, min_length=1, max_length=10_000)
    man_of_the_match_player_id: Optional[int] = None


class MatchReportResponse(MatchReportBase):
    id: int
    game_id: int
    author_id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
