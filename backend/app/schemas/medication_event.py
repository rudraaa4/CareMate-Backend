from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.models.medication_event import MedicationEventStatus


class MedicationEventStatusUpdate(BaseModel):
    # Only these two are ever client-settable. DELAYED is derived
    # automatically (TAKEN, but late); UPCOMING/MISSED are system states a
    # client should never set directly.
    status: Literal[MedicationEventStatus.TAKEN, MedicationEventStatus.SKIPPED]
    note: str | None = Field(default=None, max_length=500)


class MedicationEventResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    schedule_id: int
    scheduled_at: datetime
    status: MedicationEventStatus
    actual_taken_at: datetime | None
    note: str | None
    created_at: datetime
    updated_at: datetime
