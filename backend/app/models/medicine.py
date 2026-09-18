from __future__ import annotations

from datetime import date, datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.medication_schedule import MedicationSchedule
    from app.models.medicine_inventory import MedicineInventory
    from app.models.patient_profile import PatientProfile


class Medicine(Base):
    __tablename__ = "medicines"

    id: Mapped[int] = mapped_column(primary_key=True)
    patient_id: Mapped[int] = mapped_column(
        ForeignKey("patient_profiles.id"), nullable=False, index=True
    )

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    strength: Mapped[str | None] = mapped_column(String(100), nullable=True)
    form: Mapped[str | None] = mapped_column(String(100), nullable=True)
    instructions: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    start_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    end_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    # Soft-delete flag. DELETE /medicines/{id} sets this False rather than
    # removing the row — later phases (adherence, timeline) need history of
    # medicines the patient used to take, not just current ones.
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    patient: Mapped["PatientProfile"] = relationship(back_populates="medicines")
    schedules: Mapped[list["MedicationSchedule"]] = relationship(
        back_populates="medicine", cascade="all, delete-orphan"
    )
    # Opt-in: a Medicine may have no inventory record at all (tracking
    # isn't set up for it yet) — this stays None in that case.
    inventory: Mapped["MedicineInventory | None"] = relationship(
        back_populates="medicine", uselist=False, cascade="all, delete-orphan"
    )
