"""Deterministic adherence calculations from MedicationEvent history.

Formula: adherence % = taken_doses / eligible_expected_doses * 100

Decisions made explicitly here (the spec requires this, not left silent):

- UPCOMING events are excluded entirely — you can't be adherent or
  non-adherent about a dose that isn't due yet. "Eligible" means the dose
  has already come due, one way or another.
- DELAYED counts as TAKEN for this percentage. The patient did take the
  medicine; lateness is a separate signal (Phase 28: Adherence Pattern
  Intelligence — future work), not a correctness signal.
- SKIPPED and MISSED both count as eligible-but-not-taken, correctly
  reducing the percentage, for different underlying reasons (deliberate
  vs. passive) — both counts are reported separately so that distinction
  isn't lost.
- Zero eligible doses -> adherence_percentage is None, not 0 or 100. A
  patient with no history yet has neither succeeded nor failed.
"""

from dataclasses import dataclass
from datetime import date, datetime, timedelta

from sqlalchemy.orm import Session

from app.core.timezone import local_now
from app.models.medication_event import MedicationEvent, MedicationEventStatus
from app.models.medication_schedule import MedicationSchedule
from app.models.medicine import Medicine
from app.services.medication_event_service import refresh_missed_statuses

ADHERENT_STATUSES = {MedicationEventStatus.TAKEN, MedicationEventStatus.DELAYED}
ELIGIBLE_STATUSES = {
    MedicationEventStatus.TAKEN,
    MedicationEventStatus.DELAYED,
    MedicationEventStatus.MISSED,
    MedicationEventStatus.SKIPPED,
}


@dataclass
class AdherenceSummary:
    start_date: date
    end_date: date
    expected_doses: int
    taken_doses: int
    delayed_doses: int
    missed_doses: int
    skipped_doses: int
    adherence_percentage: float | None


class AdherenceService:
    def __init__(self, db: Session, patient_id: int):
        self.db = db
        self.patient_id = patient_id

    def calculate_period_adherence(self, start_date: date, end_date: date) -> AdherenceSummary:
        local_tz = local_now().tzinfo
        range_start = datetime.combine(start_date, datetime.min.time(), tzinfo=local_tz)
        range_end = datetime.combine(end_date, datetime.min.time(), tzinfo=local_tz) + timedelta(
            days=1
        )

        events = (
            self.db.query(MedicationEvent)
            .join(MedicationSchedule, MedicationEvent.schedule_id == MedicationSchedule.id)
            .join(Medicine, MedicationSchedule.medicine_id == Medicine.id)
            .filter(
                Medicine.patient_id == self.patient_id,
                MedicationEvent.scheduled_at >= range_start,
                MedicationEvent.scheduled_at < range_end,
            )
            .all()
        )
        # Same rule used when serving events over HTTP — a report run
        # before anyone opened the app today must still be accurate.
        refresh_missed_statuses(events, self.db)

        eligible = [e for e in events if e.status in ELIGIBLE_STATUSES]
        taken = [e for e in eligible if e.status in ADHERENT_STATUSES]
        delayed = [e for e in eligible if e.status == MedicationEventStatus.DELAYED]
        missed = [e for e in eligible if e.status == MedicationEventStatus.MISSED]
        skipped = [e for e in eligible if e.status == MedicationEventStatus.SKIPPED]

        adherence_percentage = round(len(taken) / len(eligible) * 100, 1) if eligible else None

        return AdherenceSummary(
            start_date=start_date,
            end_date=end_date,
            expected_doses=len(eligible),
            taken_doses=len(taken),
            delayed_doses=len(delayed),
            missed_doses=len(missed),
            skipped_doses=len(skipped),
            adherence_percentage=adherence_percentage,
        )

    def get_daily_summary(self, target_date: date | None = None) -> AdherenceSummary:
        target_date = target_date or local_now().date()
        return self.calculate_period_adherence(target_date, target_date)

    def get_weekly_summary(self, end_date: date | None = None) -> AdherenceSummary:
        """The 7-day period ending on (and including) end_date, default today."""
        end_date = end_date or local_now().date()
        return self.calculate_period_adherence(end_date - timedelta(days=6), end_date)
