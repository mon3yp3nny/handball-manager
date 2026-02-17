from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


# Base schemas
class NewsBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=300)
    content: str = Field(..., min_length=1, max_length=10000)
    is_published: bool = False


# Create schemas
class NewsCreate(NewsBase):
    team_id: Optional[int] = None


# Update schemas
class NewsUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=300)
    content: Optional[str] = Field(None, min_length=1, max_length=10000)
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
