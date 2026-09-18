from datetime import date, datetime, time

from pydantic import BaseModel, ConfigDict, Field

from app.models.medication_schedule import ScheduleFrequency


class MedicationScheduleCreate(BaseModel):
    time_of_day: time
    frequency: ScheduleFrequency = ScheduleFrequency.DAILY
    # Defaults to today if not supplied — "start this schedule now" is the
    # common case; still explicitly overridable for a future/backdated start.
    start_date: date = Field(default_factory=date.today)
    end_date: date | None = None


class MedicationScheduleUpdate(BaseModel):
    time_of_day: time | None = None
    frequency: ScheduleFrequency | None = None
    start_date: date | None = None
    end_date: date | None = None


class MedicationScheduleResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    medicine_id: int
    time_of_day: time
    frequency: ScheduleFrequency
    start_date: date
    end_date: date | None
    active: bool
    created_at: datetime
    updated_at: datetime
