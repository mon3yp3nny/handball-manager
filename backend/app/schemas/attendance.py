from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum


class AttendanceStatus(str, Enum):
    PRESENT = "present"
    ABSENT = "absent"
    EXCUSED = "excused"
    PENDING = "pending"


# Base schemas
class AttendanceBase(BaseModel):
    status: AttendanceStatus = AttendanceStatus.PENDING
    notes: Optional[str] = Field(None, max_length=500)


# Create schemas
class AttendanceCreate(AttendanceBase):
    player_id: int
    game_id: Optional[int] = None
    event_id: Optional[int] = None


# Update schemas
class AttendanceUpdate(BaseModel):
    status: Optional[AttendanceStatus] = None
    notes: Optional[str] = Field(None, max_length=500)


# Response schemas
class AttendanceResponse(AttendanceBase):
    id: int
    player_id: int
    game_id: Optional[int]
    event_id: Optional[int]
    recorded_by: Optional[int]
    recorded_at: datetime

    class Config:
        from_attributes = True


class AttendanceWithPlayer(AttendanceResponse):
    player_name: Optional[str] = None
    player_jersey: Optional[int] = None

    class Config:
        from_attributes = True


# Bulk update
class BulkAttendanceUpdate(BaseModel):
    player_ids: List[int] = Field(..., min_length=1)
    status: AttendanceStatus
    notes: Optional[str] = Field(None, max_length=500)
