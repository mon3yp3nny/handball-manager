from pydantic import BaseModel
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
    notes: Optional[str] = None


# Create schemas
class AttendanceCreate(AttendanceBase):
    player_id: int
    game_id: Optional[int] = None
    event_id: Optional[int] = None


# Update schemas
class AttendanceUpdate(BaseModel):
    status: Optional[AttendanceStatus] = None
    notes: Optional[str] = None


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
    player_ids: List[int]
    status: AttendanceStatus
    notes: Optional[str] = None
