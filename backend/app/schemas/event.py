from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from enum import Enum


class EventType(str, Enum):
    TRAINING = "training"
    MEETING = "meeting"
    TOURNAMENT = "tournament"
    OTHER = "other"


class EventVisibility(str, Enum):
    TEAM = "team"
    CLUB_WIDE = "club_wide"
    AGE_GROUP = "age_group"


# Base schemas
class EventBase(BaseModel):
    title: str
    description: Optional[str] = None
    event_type: EventType = EventType.TRAINING
    visibility: EventVisibility = EventVisibility.TEAM
    location: Optional[str] = None
    start_time: datetime
    end_time: datetime


# Create schemas
class EventCreate(EventBase):
    team_id: Optional[int] = None


# Update schemas
class EventUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    event_type: Optional[EventType] = None
    visibility: Optional[EventVisibility] = None
    team_id: Optional[int] = None
    location: Optional[str] = None
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
