from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class HealthNoteCreate(BaseModel):
    text: str = Field(min_length=1, max_length=2000)
    recorded_at: datetime | None = None  # defaults to now if omitted
    medicine_id: int | None = None


class HealthNoteUpdate(BaseModel):
    text: str | None = Field(default=None, min_length=1, max_length=2000)
    recorded_at: datetime | None = None
    medicine_id: int | None = None


class HealthNoteResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    text: str
    recorded_at: datetime
    medicine_id: int | None
    created_at: datetime
    updated_at: datetime
