"""Business logic for medication events — deliberately separated from
app/api/routes/medication_events.py (HTTP concerns) so the same rules
(what counts as MISSED, what counts as DELAYED) can be reused elsewhere,
e.g. by AdherenceService, without duplicating them.
"""

from datetime import date, datetime, timedelta

from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.core.timezone import local_now
from app.models.medication_event import MedicationEvent, MedicationEventStatus
from app.models.medication_schedule import MedicationSchedule
from app.models.medicine import Medicine

# A TAKEN event recorded more than this long after its scheduled time
# becomes DELAYED instead. An UPCOMING event this far past its scheduled
# time with no action becomes MISSED. Both are simple, documented
# thresholds — not something the spec pins down, so these are our decision,
# recorded here and in DEVELOPMENT_PROGRESS.md.
DELAYED_THRESHOLD = timedelta(minutes=30)
MISSED_THRESHOLD = timedelta(hours=2)

# States the patient has explicitly confirmed — once set, PATCH .../status
# refuses to change them further.
TERMINAL_STATUSES = {
    MedicationEventStatus.TAKEN,
    MedicationEventStatus.DELAYED,
    MedicationEventStatus.SKIPPED,
}


def generate_todays_events(patient_id: int, db: Session) -> None:
    """Idempotent: safe to call on every GET. Creates an UPCOMING event for
    today for each active schedule of an active medicine, if one doesn't
    already exist (schedule_id, scheduled_at) — also enforced by a DB
    unique constraint as a second line of defense."""
    today = date.today()
    local_tz = local_now().tzinfo

    active_schedules = (
        db.query(MedicationSchedule)
        .join(Medicine, MedicationSchedule.medicine_id == Medicine.id)
        .filter(
            Medicine.patient_id == patient_id,
            Medicine.active.is_(True),
            MedicationSchedule.active.is_(True),
            MedicationSchedule.start_date <= today,
            or_(MedicationSchedule.end_date.is_(None), MedicationSchedule.end_date >= today),
        )
        .all()
    )

    for schedule in active_schedules:
        scheduled_at = datetime.combine(today, schedule.time_of_day, tzinfo=local_tz)
        exists = (
            db.query(MedicationEvent)
            .filter(
                MedicationEvent.schedule_id == schedule.id,
                MedicationEvent.scheduled_at == scheduled_at,
            )
            .first()
        )
        if exists is None:
            db.add(MedicationEvent(schedule_id=schedule.id, scheduled_at=scheduled_at))

    db.commit()


def get_or_create_todays_events(patient_id: int, db: Session) -> list[MedicationEvent]:
    """Ensures today's events exist, then returns them, missed statuses
    refreshed. Used by both GET /medication-events/today and the Phase 10
    dashboard — factored out here specifically so the dashboard doesn't
    duplicate this query, per that phase's Definition of Done."""
    generate_todays_events(patient_id, db)

    today = date.today()
    local_tz = local_now().tzinfo
    range_start = datetime.combine(today, datetime.min.time(), tzinfo=local_tz)
    range_end = range_start + timedelta(days=1)

    events = (
        db.query(MedicationEvent)
        .join(MedicationSchedule, MedicationEvent.schedule_id == MedicationSchedule.id)
        .join(Medicine, MedicationSchedule.medicine_id == Medicine.id)
        .filter(
            Medicine.patient_id == patient_id,
            MedicationEvent.scheduled_at >= range_start,
            MedicationEvent.scheduled_at < range_end,
        )
        .order_by(MedicationEvent.scheduled_at)
        .all()
    )

    refresh_missed_statuses(events, db)
    return events


def refresh_missed_statuses(events: list[MedicationEvent], db: Session) -> None:
    """Lazily flips any UPCOMING event that's past the missed threshold.
    No cron job — this runs whenever events are read (see Phase 24 for why
    a real scheduler isn't built yet). Used both when serving events over
    HTTP and when computing adherence, so a report is never wrong just
    because nobody happened to open the app and trigger a refresh."""
    now = local_now()
    changed = False
    for event in events:
        if event.status == MedicationEventStatus.UPCOMING and now - event.scheduled_at > MISSED_THRESHOLD:
            event.status = MedicationEventStatus.MISSED
            changed = True
    if changed:
        db.commit()


def classify_taken_status(scheduled_at: datetime, taken_at: datetime) -> MedicationEventStatus:
    """TAKEN vs DELAYED is purely a function of how late `taken_at` is
    relative to `scheduled_at` — never something the client chooses."""
    if taken_at - scheduled_at > DELAYED_THRESHOLD:
        return MedicationEventStatus.DELAYED
    return MedicationEventStatus.TAKEN


def mark_taken(event: MedicationEvent, db: Session) -> None:
    """MedicationEventService -> InventoryService, per the spec's own
    description of this flow. Mutates event in place (status,
    actual_taken_at) and decrements the medicine's inventory if it has
    one. Callers must only invoke this when event.status is not already
    in TERMINAL_STATUSES (see the route's guard) — that's what makes this
    reachable at most once per event, so inventory is never decremented
    twice for the same dose.
    """
    from app.services.inventory_service import InventoryService  # avoid a circular import

    now = local_now()
    event.actual_taken_at = now
    event.status = classify_taken_status(event.scheduled_at, now)

    InventoryService(db).decrement_for_taken_event(event.schedule.medicine_id)
