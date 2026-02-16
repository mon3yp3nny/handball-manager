from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from enum import Enum


class ActivityType(str, Enum):
    LOGIN = "login"
    LOGOUT = "logout"
    PASSWORD_CHANGE = "password_change"
    PROFILE_UPDATE = "profile_update"
    CREATED = "created"
    UPDATED = "updated"
    DELETED = "deleted"
    ROLE_CHANGE = "role_change"


# Create schemas
class UserActivityCreate(BaseModel):
    activity_type: ActivityType
    description: Optional[str] = None


# Response schemas
class UserActivityResponse(BaseModel):
    id: int
    user_id: int
    activity_type: ActivityType
    description: Optional[str]
    ip_address: Optional[str]
    user_agent: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True


class UserActivityWithUser(UserActivityResponse):
    user_email: Optional[str] = None
    user_name: Optional[str] = None
    
    class Config:
        from_attributes = True
