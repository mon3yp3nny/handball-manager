"""Common pagination schemas."""
from pydantic import BaseModel
from typing import List, TypeVar, Generic


class PaginationParams(BaseModel):
    """Query parameters for pagination."""
    skip: int = 0
    limit: int = 100


class PaginatedResponse(BaseModel):
    """Base paginated response model."""
    total: int
    skip: int
    limit: int
    items: list
    
    class Config:
        from_attributes = True


T = TypeVar('T')


class PaginatedResponseGeneric(BaseModel, Generic[T]):
    """Generic paginated response that can be used with any item type."""
    total: int
    skip: int
    limit: int
    items: List[T]
    
    class Config:
        from_attributes = True
