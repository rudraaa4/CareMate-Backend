from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field

# Note: no patient_id field anywhere here. The patient is always derived
# server-side from the authenticated user, never accepted from the client
# (CAREMATE_MASTER_SPEC.md section 9, rule 1).


class MedicineCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    strength: str | None = Field(default=None, max_length=100)
    form: str | None = Field(default=None, max_length=100)
    instructions: str | None = Field(default=None, max_length=1000)
    start_date: date | None = None
    end_date: date | None = None


class MedicineUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    strength: str | None = Field(default=None, max_length=100)
    form: str | None = Field(default=None, max_length=100)
    instructions: str | None = Field(default=None, max_length=1000)
    start_date: date | None = None
    end_date: date | None = None


class MedicineResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    strength: str | None
    form: str | None
    instructions: str | None
    start_date: date | None
    end_date: date | None
    active: bool
    created_at: datetime
    updated_at: datetime
