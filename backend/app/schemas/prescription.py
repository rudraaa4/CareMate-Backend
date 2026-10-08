from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.prescription import PrescriptionSource


class PrescriptionCreate(BaseModel):
    prescription_date: date
    doctor_name: str | None = Field(default=None, max_length=255)
    hospital_name: str | None = Field(default=None, max_length=255)
    notes: str | None = Field(default=None, max_length=2000)
    document_id: int | None = None


class PrescriptionUpdate(BaseModel):
    prescription_date: date | None = None
    doctor_name: str | None = Field(default=None, max_length=255)
    hospital_name: str | None = Field(default=None, max_length=255)
    notes: str | None = Field(default=None, max_length=2000)
    document_id: int | None = None

    @field_validator("prescription_date")
    @classmethod
    def date_cannot_be_cleared(cls, value: date | None) -> date:
        # The column is NOT NULL; an explicit null would otherwise reach the
        # database and surface as a 500 instead of a clear 422.
        if value is None:
            raise ValueError("prescription_date cannot be null")
        return value


class PrescriptionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    prescription_date: date
    doctor_name: str | None
    hospital_name: str | None
    notes: str | None
    document_id: int | None
    source: PrescriptionSource
    created_at: datetime
    updated_at: datetime
