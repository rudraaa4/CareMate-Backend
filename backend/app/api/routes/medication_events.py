from datetime import date, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.core.database import get_db
from app.core.timezone import local_now
from app.models.medication_event import MedicationEvent, MedicationEventStatus
from app.models.medication_schedule import MedicationSchedule
from app.models.medicine import Medicine
from app.models.user import User
from app.schemas.medication_event import MedicationEventResponse, MedicationEventStatusUpdate
from app.services.medication_event_service import (
    TERMINAL_STATUSES,
    classify_taken_status,
    generate_todays_events,
    refresh_missed_statuses,
)

router = APIRouter(prefix="/api/v1/medication-events", tags=["Medication Events"])


@router.get("/today", response_model=list[MedicationEventResponse])
def get_todays_events(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> list[MedicationEvent]:
    patient_id = current_user.patient_profile.id
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

    refresh_missed_statuses([event], db)
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
        now = local_now()
        event.actual_taken_at = now
        event.status = classify_taken_status(event.scheduled_at, now)
    else:
        event.status = MedicationEventStatus.SKIPPED

    if status_in.note is not None:
        event.note = status_in.note

    db.commit()
    db.refresh(event)
    return event
