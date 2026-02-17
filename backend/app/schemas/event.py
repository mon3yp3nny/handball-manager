from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum


class EventType(str, Enum):
    TRAINING = "training"
    GAME = "game"
    MEETING = "meeting"
    TOURNAMENT = "tournament"
    OTHER = "other"


class EventVisibility(str, Enum):
    TEAM = "team"
    CLUB_WIDE = "club_wide"
    AGE_GROUP = "age_group"


# Base schemas
class EventBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=2000)
    event_type: EventType = EventType.TRAINING
    visibility: EventVisibility = EventVisibility.TEAM
    location: Optional[str] = Field(None, max_length=300)
    start_time: datetime
    end_time: datetime


# Create schemas
class EventCreate(EventBase):
    team_id: Optional[int] = None


# Update schemas
class EventUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=2000)
    event_type: Optional[EventType] = None
    visibility: Optional[EventVisibility] = None
    team_id: Optional[int] = None
    location: Optional[str] = Field(None, max_length=300)
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None


# Response schemas
class EventResponse(EventBase):
    id: int
    team_id: Optional[int]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class EventWithTeam(EventResponse):
    team_name: Optional[str] = None

    class Config:
        from_attributes = True
