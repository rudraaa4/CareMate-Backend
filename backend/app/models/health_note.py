from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.medicine import Medicine
    from app.models.patient_profile import PatientProfile


class HealthNote(Base):
    __tablename__ = "health_notes"

    id: Mapped[int] = mapped_column(primary_key=True)
    patient_id: Mapped[int] = mapped_column(
        ForeignKey("patient_profiles.id"), nullable=False, index=True
    )
    # Optional tag linking a note to a specific medicine (e.g. "nausea
    # after evening dose"). Never a diagnosis — plain text only.
    medicine_id: Mapped[int | None] = mapped_column(ForeignKey("medicines.id"), nullable=True)

    text: Mapped[str] = mapped_column(String(2000), nullable=False)
    # Client-settable, unlike MedicationEvent.actual_taken_at — the patient
    # is the authority on when an observation actually happened ("I had a
    # headache yesterday evening"), not something to guard against spoofing.
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    patient: Mapped["PatientProfile"] = relationship(back_populates="health_notes")
    medicine: Mapped["Medicine | None"] = relationship()
