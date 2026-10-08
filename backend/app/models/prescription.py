from __future__ import annotations

import enum
from datetime import date, datetime
from typing import TYPE_CHECKING

from sqlalchemy import Date, DateTime, Enum, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.medical_document import MedicalDocument
    from app.models.patient_profile import PatientProfile


class PrescriptionSource(str, enum.Enum):
    # Where the record came from. Never client-settable: later phases add
    # values (AI-extracted, doctor-issued) whose meaning depends on the
    # server being the only one who can assign them.
    MANUAL = "manual"
    DOCUMENT_UPLOAD = "document_upload"


class Prescription(Base):
    __tablename__ = "prescriptions"

    id: Mapped[int] = mapped_column(primary_key=True)
    patient_id: Mapped[int] = mapped_column(
        ForeignKey("patient_profiles.id"), nullable=False, index=True
    )
    # Optional link to the scanned/photographed prescription in the vault.
    # The document stays a generic file; this row is the healthcare record.
    document_id: Mapped[int | None] = mapped_column(
        ForeignKey("medical_documents.id"), nullable=True
    )

    # Free text for now — doctors/hospitals become real entities in later phases.
    doctor_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    hospital_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    prescription_date: Mapped[date] = mapped_column(Date, nullable=False)
    notes: Mapped[str | None] = mapped_column(String(2000), nullable=True)
    source: Mapped[PrescriptionSource] = mapped_column(
        Enum(PrescriptionSource, values_callable=lambda enum_cls: [m.value for m in enum_cls]),
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    patient: Mapped["PatientProfile"] = relationship(back_populates="prescriptions")
    document: Mapped["MedicalDocument | None"] = relationship()
