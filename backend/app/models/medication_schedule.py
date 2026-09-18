from __future__ import annotations

import enum
from datetime import date, datetime, time
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Date, DateTime, Enum, ForeignKey, Time, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.medicine import Medicine


class ScheduleFrequency(str, enum.Enum):
    """Only DAILY exists for now — the spec explicitly says not to
    over-engineer recurrence yet. WEEKLY/EVERY_OTHER_DAY etc. can be added
    later without a schema rewrite, same pattern as UserRole."""

    DAILY = "daily"


class MedicationSchedule(Base):
    __tablename__ = "medication_schedules"

    id: Mapped[int] = mapped_column(primary_key=True)
    medicine_id: Mapped[int] = mapped_column(
        ForeignKey("medicines.id"), nullable=False, index=True
    )

    # One row per time-of-day. "Metformin at 08:00 and 20:00" is two rows
    # sharing one medicine_id, not one row holding a list of times.
    time_of_day: Mapped[time] = mapped_column(Time, nullable=False)
    frequency: Mapped[ScheduleFrequency] = mapped_column(
        Enum(ScheduleFrequency, values_callable=lambda enum_cls: [m.value for m in enum_cls]),
        default=ScheduleFrequency.DAILY,
        nullable=False,
    )
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    medicine: Mapped["Medicine"] = relationship(back_populates="schedules")
