from __future__ import annotations

import enum
from datetime import date, datetime
from typing import TYPE_CHECKING

from sqlalchemy import Date, DateTime, Enum, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.patient_profile import PatientProfile


class DocumentType(str, enum.Enum):
    PRESCRIPTION = "prescription"
    LAB_REPORT = "lab_report"
    SCAN_REPORT = "scan_report"
    DISCHARGE_SUMMARY = "discharge_summary"
    DOCTOR_NOTE = "doctor_note"
    OTHER = "other"


class MedicalDocument(Base):
    __tablename__ = "medical_documents"

    id: Mapped[int] = mapped_column(primary_key=True)
    patient_id: Mapped[int] = mapped_column(
        ForeignKey("patient_profiles.id"), nullable=False, index=True
    )

    document_type: Mapped[DocumentType] = mapped_column(
        Enum(DocumentType, values_callable=lambda enum_cls: [m.value for m in enum_cls]),
        nullable=False,
    )
    # Server-generated (uuid4 hex + a whitelisted extension) — never derived
    # from the client's filename. This is the actual path-traversal defense;
    # see app/storage/local.py and app/api/routes/documents.py.
    storage_key: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    # Metadata only — display purposes. Never used to build a filesystem path.
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    content_type: Mapped[str] = mapped_column(String(100), nullable=False)
    document_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    description: Mapped[str | None] = mapped_column(String(1000), nullable=True)

    uploaded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    patient: Mapped["PatientProfile"] = relationship(back_populates="medical_documents")
