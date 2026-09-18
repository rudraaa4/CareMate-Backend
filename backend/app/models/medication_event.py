from __future__ import annotations

import enum
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum, ForeignKey, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.medication_schedule import MedicationSchedule


class MedicationEventStatus(str, enum.Enum):
    """Two kinds of status, see app/api/routes/medication_events.py for the
    exact transition rules:

    System-inferred (can still change):  UPCOMING, MISSED
    Patient-confirmed (terminal once set): TAKEN, DELAYED, SKIPPED
    """

    UPCOMING = "upcoming"
    TAKEN = "taken"
    MISSED = "missed"
    SKIPPED = "skipped"
    DELAYED = "delayed"


class MedicationEvent(Base):
    __tablename__ = "medication_events"
    __table_args__ = (
        # Guards event generation being idempotent at the DB level, not just
        # in application logic — calling "generate today's events" twice
        # concurrently can't create duplicates for the same schedule+time.
        UniqueConstraint("schedule_id", "scheduled_at", name="uq_schedule_scheduled_at"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    schedule_id: Mapped[int] = mapped_column(
        ForeignKey("medication_schedules.id"), nullable=False, index=True
    )

    scheduled_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    status: Mapped[MedicationEventStatus] = mapped_column(
        Enum(
            MedicationEventStatus,
            values_callable=lambda enum_cls: [m.value for m in enum_cls],
        ),
        default=MedicationEventStatus.UPCOMING,
        nullable=False,
    )
    actual_taken_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    note: Mapped[str | None] = mapped_column(String(500), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    schedule: Mapped["MedicationSchedule"] = relationship(back_populates="events")
