"""Schemas for the player-availability endpoint."""
from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, Field, model_validator

from app.models.player_availability import AvailabilityReason


class AvailabilityBase(BaseModel):
    from_date: date
    to_date: Optional[date] = None
    reason: AvailabilityReason = AvailabilityReason.OTHER
    note: Optional[str] = Field(None, max_length=500)
    is_medical: bool = False

    @model_validator(mode="after")
    def _validate_range(self):
        if self.to_date is not None and self.to_date < self.from_date:
            raise ValueError("to_date must be on or after from_date")
        return self


class AvailabilityCreate(AvailabilityBase):
    pass


class AvailabilityUpdate(BaseModel):
    from_date: Optional[date] = None
    to_date: Optional[date] = None
    reason: Optional[AvailabilityReason] = None
    note: Optional[str] = Field(None, max_length=500)
    is_medical: Optional[bool] = None


class AvailabilityResponse(AvailabilityBase):
    id: int
    player_id: int
    created_by: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
