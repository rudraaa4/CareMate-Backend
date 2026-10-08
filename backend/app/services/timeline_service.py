"""Aggregates a patient's care history into one ordered list of TimelineItems.

Deliberately not a timeline table (the spec warns against one): every
source already lives in its own table with its own ownership rules, so the
timeline is a read-only view assembled on request. There is nothing to keep
in sync and nothing that can drift out of date.

Sources included now: prescriptions, document uploads, treatment starts and
ends (from medicines), health notes, and monthly adherence summaries.
"Future visits" is in the spec's list but no visit model exists yet, so it
is not included; it will be one more `_*_items` method when it does.

Decisions made explicitly:

- A document that a prescription links to is shown once, as part of the
  prescription item, not again as a separate upload.
- A medicine with no start_date is shown as starting on the day it was
  added to CareMate; the real start is unknown and a medicine should not
  vanish from the story because an optional field was left empty.
- Adherence is summarized per calendar month, using the same
  AdherenceService (and so the same formula) as the dashboard. A month
  with no eligible doses produces no item; the current month is dated
  today because it is still in progress.
"""

import calendar
from datetime import date, datetime, time

from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from app.core.timezone import local_now
from app.models.health_note import HealthNote
from app.models.medical_document import DocumentType, MedicalDocument
from app.models.medication_event import MedicationEvent
from app.models.medication_schedule import MedicationSchedule
from app.models.medicine import Medicine
from app.models.prescription import Prescription
from app.schemas.timeline import TimelineItem, TimelineItemType
from app.services.adherence_service import AdherenceService

_DOCUMENT_TITLES = {
    DocumentType.PRESCRIPTION: "Prescription document uploaded",
    DocumentType.LAB_REPORT: "Lab report uploaded",
    DocumentType.SCAN_REPORT: "Scan report uploaded",
    DocumentType.DISCHARGE_SUMMARY: "Discharge summary uploaded",
    DocumentType.DOCTOR_NOTE: "Doctor note uploaded",
    DocumentType.OTHER: "Document uploaded",
}


def _at_local_midnight(day: date) -> datetime:
    return datetime.combine(day, time.min, tzinfo=local_now().tzinfo)


class TimelineService:
    def __init__(self, db: Session, patient_id: int):
        self.db = db
        self.patient_id = patient_id

    def get_timeline(self, newest_first: bool = True) -> list[TimelineItem]:
        items = [
            *self._prescription_items(),
            *self._document_items(),
            *self._treatment_items(),
            *self._health_note_items(),
            *self._adherence_items(),
        ]
        # reference_id/type break ties between items on the same instant so
        # the order is stable from one request to the next.
        items.sort(
            key=lambda item: (item.occurred_at, item.type.value, item.reference_id or 0),
            reverse=newest_first,
        )
        return items

    def _prescription_items(self) -> list[TimelineItem]:
        prescriptions = self.db.query(Prescription).filter(Prescription.patient_id == self.patient_id).all()
        items = []
        for p in prescriptions:
            title = f"Prescription from {p.doctor_name}" if p.doctor_name else "Prescription"
            details = [part for part in (p.hospital_name, p.notes) if part]
            items.append(
                TimelineItem(
                    type=TimelineItemType.PRESCRIPTION,
                    occurred_at=_at_local_midnight(p.prescription_date),
                    title=title,
                    description=" - ".join(details) or None,
                    reference_id=p.id,
                    document_id=p.document_id,
                )
            )
        return items

    def _document_items(self) -> list[TimelineItem]:
        linked_to_prescription = select(Prescription.document_id).where(
            Prescription.patient_id == self.patient_id, Prescription.document_id.isnot(None)
        )
        documents = (
            self.db.query(MedicalDocument)
            .filter(
                MedicalDocument.patient_id == self.patient_id,
                MedicalDocument.id.notin_(linked_to_prescription),
            )
            .all()
        )
        return [
            TimelineItem(
                type=TimelineItemType.DOCUMENT,
                occurred_at=(
                    _at_local_midnight(d.document_date) if d.document_date else d.uploaded_at
                ),
                title=_DOCUMENT_TITLES[d.document_type],
                description=d.description or d.original_filename,
                reference_id=d.id,
                document_id=d.id,
            )
            for d in documents
        ]

    def _treatment_items(self) -> list[TimelineItem]:
        medicines = self.db.query(Medicine).filter(Medicine.patient_id == self.patient_id).all()
        items = []
        for m in medicines:
            label = f"{m.name} {m.strength}" if m.strength else m.name
            started = m.start_date or m.created_at.astimezone(local_now().tzinfo).date()
            items.append(
                TimelineItem(
                    type=TimelineItemType.TREATMENT_STARTED,
                    occurred_at=_at_local_midnight(started),
                    title=f"Started {label}",
                    description=m.instructions,
                    reference_id=m.id,
                )
            )
            if m.end_date is not None:
                items.append(
                    TimelineItem(
                        type=TimelineItemType.TREATMENT_ENDED,
                        occurred_at=_at_local_midnight(m.end_date),
                        title=f"Ended {label}",
                        reference_id=m.id,
                    )
                )
        return items

    def _health_note_items(self) -> list[TimelineItem]:
        notes = (
            self.db.query(HealthNote)
            .options(joinedload(HealthNote.medicine))
            .filter(HealthNote.patient_id == self.patient_id)
            .all()
        )
        return [
            TimelineItem(
                type=TimelineItemType.HEALTH_NOTE,
                occurred_at=n.recorded_at,
                title=f"Note about {n.medicine.name}" if n.medicine else "Health note",
                description=n.text,
                reference_id=n.id,
            )
            for n in notes
        ]

    def _adherence_items(self) -> list[TimelineItem]:
        first_event_at = (
            self.db.query(func.min(MedicationEvent.scheduled_at))
            .join(MedicationSchedule, MedicationEvent.schedule_id == MedicationSchedule.id)
            .join(Medicine, MedicationSchedule.medicine_id == Medicine.id)
            .filter(Medicine.patient_id == self.patient_id)
            .scalar()
        )
        if first_event_at is None:
            return []

        today = local_now().date()
        first = first_event_at.astimezone(local_now().tzinfo).date()
        service = AdherenceService(self.db, self.patient_id)

        items = []
        year, month = first.year, first.month
        while (year, month) <= (today.year, today.month):
            month_start = date(year, month, 1)
            month_end = date(year, month, calendar.monthrange(year, month)[1])
            summary = service.calculate_period_adherence(month_start, month_end)
            if summary.expected_doses > 0:
                details = f"{summary.taken_doses} of {summary.expected_doses} doses taken"
                if summary.missed_doses:
                    details += f", {summary.missed_doses} missed"
                if summary.skipped_doses:
                    details += f", {summary.skipped_doses} skipped"
                items.append(
                    TimelineItem(
                        type=TimelineItemType.ADHERENCE_SUMMARY,
                        occurred_at=_at_local_midnight(min(month_end, today)),
                        title=f"{summary.adherence_percentage:g}% adherence in {month_start:%B %Y}",
                        description=details,
                    )
                )
            year, month = (year + 1, 1) if month == 12 else (year, month + 1)
        return items
