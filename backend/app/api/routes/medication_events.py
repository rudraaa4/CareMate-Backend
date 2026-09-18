from datetime import date, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.core.database import get_db
from app.models.medication_event import MedicationEvent, MedicationEventStatus
from app.models.medication_schedule import MedicationSchedule
from app.models.medicine import Medicine
from app.models.user import User
from app.schemas.medication_event import MedicationEventResponse, MedicationEventStatusUpdate

router = APIRouter(prefix="/api/v1/medication-events", tags=["Medication Events"])

# A TAKEN event recorded more than this long after its scheduled time
# becomes DELAYED instead. An UPCOMING event this far past its scheduled
# time with no action becomes MISSED. Both are simple, documented
# thresholds — not something the spec pins down, so these are our decision,
# recorded here and in DEVELOPMENT_PROGRESS.md.
DELAYED_THRESHOLD = timedelta(minutes=30)
MISSED_THRESHOLD = timedelta(hours=2)

# States the patient has explicitly confirmed — once set, PATCH .../status
# refuses to change them further (see update_event_status below).
TERMINAL_STATUSES = {
    MedicationEventStatus.TAKEN,
    MedicationEventStatus.DELAYED,
    MedicationEventStatus.SKIPPED,
}


def _local_now() -> datetime:
    """Server-local time, used consistently for 'today' and 'now' below.

    Simplification: assumes every patient is in the server's timezone.
    CAREMATE_MASTER_SPEC.md section 16 explicitly flags this as something
    architecture shouldn't assume forever — revisit once patient-level
    timezones exist (not needed yet: this is a single-region prototype).
    """
    return datetime.now().astimezone()


def _generate_todays_events(patient_id: int, db: Session) -> None:
    """Idempotent: safe to call on every GET. Creates an UPCOMING event for
    today for each active schedule of an active medicine, if one doesn't
    already exist (schedule_id, scheduled_at) — also enforced by a DB
    unique constraint as a second line of defense."""
    today = date.today()
    local_tz = _local_now().tzinfo

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


def _refresh_missed_statuses(events: list[MedicationEvent], db: Session) -> None:
    """Lazily flips any UPCOMING event that's past the missed threshold.
    No cron job — this runs whenever events are read (see Phase 24 for why
    a real scheduler isn't built yet)."""
    now = _local_now()
    changed = False
    for event in events:
        if event.status == MedicationEventStatus.UPCOMING and now - event.scheduled_at > MISSED_THRESHOLD:
            event.status = MedicationEventStatus.MISSED
            changed = True
    if changed:
        db.commit()


@router.get("/today", response_model=list[MedicationEventResponse])
def get_todays_events(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> list[MedicationEvent]:
    patient_id = current_user.patient_profile.id
    _generate_todays_events(patient_id, db)

    today = date.today()
    local_tz = _local_now().tzinfo
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

    _refresh_missed_statuses(events, db)
    return events


def get_owned_event(
    event_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> MedicationEvent:
    """Two joins deep: Event -> Schedule -> Medicine -> patient_id. Same
    404-not-403 rule as every owned resource so far."""
    event = (
        db.query(MedicationEvent)
        .join(MedicationSchedule, MedicationEvent.schedule_id == MedicationSchedule.id)
        .join(Medicine, MedicationSchedule.medicine_id == Medicine.id)
        .filter(
            MedicationEvent.id == event_id,
            Medicine.patient_id == current_user.patient_profile.id,
        )
        .first()
    )
    if event is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")

    _refresh_missed_statuses([event], db)
    return event


@router.patch("/{event_id}/status", response_model=MedicationEventResponse)
def update_event_status(
    status_in: MedicationEventStatusUpdate,
    event: MedicationEvent = Depends(get_owned_event),
    db: Session = Depends(get_db),
) -> MedicationEvent:
    if event.status in TERMINAL_STATUSES:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Event is already {event.status.value} and cannot be changed",
        )

    if status_in.status == MedicationEventStatus.TAKEN:
        now = _local_now()
        event.actual_taken_at = now
        # Late enough that it's DELAYED, not a clean TAKEN.
        event.status = (
            MedicationEventStatus.DELAYED
            if now - event.scheduled_at > DELAYED_THRESHOLD
            else MedicationEventStatus.TAKEN
        )
    else:
        event.status = MedicationEventStatus.SKIPPED

    if status_in.note is not None:
        event.note = status_in.note

    db.commit()
    db.refresh(event)
    return event
