from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field


class PatientProfileUpdate(BaseModel):
    """All fields optional: PATCH only changes what's actually sent (see
    exclude_unset=True in the route) — omitting a field leaves it untouched."""

    full_name: str | None = Field(default=None, max_length=255)
    date_of_birth: date | None = None
    phone: str | None = Field(default=None, max_length=30)


class PatientProfileResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    full_name: str | None
    date_of_birth: date | None
    phone: str | None
    created_at: datetime
    updated_at: datetime
