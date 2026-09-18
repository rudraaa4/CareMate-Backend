from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.api.routes.medicines import get_owned_medicine
from app.core.database import get_db
from app.models.medication_schedule import MedicationSchedule
from app.models.medicine import Medicine
from app.models.user import User
from app.schemas.medication_schedule import (
    MedicationScheduleCreate,
    MedicationScheduleResponse,
    MedicationScheduleUpdate,
)

router = APIRouter(prefix="/api/v1", tags=["Medication Schedules"])


def get_owned_schedule(
    schedule_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> MedicationSchedule:
    """A schedule has no patient_id of its own — ownership flows through
    its medicine (Schedule -> Medicine -> PatientProfile), so this needs a
    join, unlike get_owned_medicine which filters a direct column. Same
    404-not-403 rule as Phase 5: don't confirm the schedule exists."""
    schedule = (
        db.query(MedicationSchedule)
        .join(Medicine, MedicationSchedule.medicine_id == Medicine.id)
        .filter(
            MedicationSchedule.id == schedule_id,
            Medicine.patient_id == current_user.patient_profile.id,
        )
        .first()
    )
    if schedule is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Schedule not found")
    return schedule


@router.post(
    "/medicines/{medicine_id}/schedules",
    response_model=MedicationScheduleResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_schedule(
    schedule_in: MedicationScheduleCreate,
    medicine: Medicine = Depends(get_owned_medicine),
    db: Session = Depends(get_db),
) -> MedicationSchedule:
    schedule = MedicationSchedule(medicine_id=medicine.id, **schedule_in.model_dump())
    db.add(schedule)
    db.commit()
    db.refresh(schedule)
    return schedule


@router.get("/medicines/{medicine_id}/schedules", response_model=list[MedicationScheduleResponse])
def list_schedules(
    include_archived: bool = False,
    medicine: Medicine = Depends(get_owned_medicine),
    db: Session = Depends(get_db),
) -> list[MedicationSchedule]:
    query = db.query(MedicationSchedule).filter(MedicationSchedule.medicine_id == medicine.id)
    if not include_archived:
        query = query.filter(MedicationSchedule.active.is_(True))
    return query.order_by(MedicationSchedule.time_of_day).all()


@router.patch("/schedules/{schedule_id}", response_model=MedicationScheduleResponse)
def update_schedule(
    schedule_in: MedicationScheduleUpdate,
    schedule: MedicationSchedule = Depends(get_owned_schedule),
    db: Session = Depends(get_db),
) -> MedicationSchedule:
    updates = schedule_in.model_dump(exclude_unset=True)
    for field, value in updates.items():
        setattr(schedule, field, value)
    db.commit()
    db.refresh(schedule)
    return schedule


@router.delete("/schedules/{schedule_id}", response_model=MedicationScheduleResponse)
def archive_schedule(
    schedule: MedicationSchedule = Depends(get_owned_schedule), db: Session = Depends(get_db)
) -> MedicationSchedule:
    schedule.active = False
    db.commit()
    db.refresh(schedule)
    return schedule
