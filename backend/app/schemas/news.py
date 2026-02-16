from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


# Base schemas
class NewsBase(BaseModel):
    title: str
    content: str
    is_published: bool = False


# Create schemas
class NewsCreate(NewsBase):
    team_id: Optional[int] = None


# Update schemas
class NewsUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    is_published: Optional[bool] = None


# Publish
class NewsPublish(BaseModel):
    is_published: bool = True


# Response schemas
class NewsResponse(NewsBase):
    id: int
    team_id: Optional[int]
    author_id: int
    published_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class NewsWithAuthor(NewsResponse):
    author_name: Optional[str] = None
    team_name: Optional[str] = None
    
    class Config:
        from_attributes = True
