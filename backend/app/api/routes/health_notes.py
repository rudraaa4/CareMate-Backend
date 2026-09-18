from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.core.database import get_db
from app.core.timezone import local_now
from app.models.health_note import HealthNote
from app.models.medicine import Medicine
from app.models.user import User
from app.schemas.health_note import HealthNoteCreate, HealthNoteResponse, HealthNoteUpdate

router = APIRouter(prefix="/api/v1/health-notes", tags=["Health Notes"])


def _validate_medicine_ownership(medicine_id: int | None, patient_id: int, db: Session) -> None:
    """medicine_id arrives inside the request body, not the URL — a
    client could try to tag a note with someone else's medicine. Reject
    with 400 (an invalid request value), not 404 (that's reserved for the
    primary resource in the URL, which for these routes is the note
    itself)."""
    if medicine_id is None:
        return
    medicine = (
        db.query(Medicine)
        .filter(Medicine.id == medicine_id, Medicine.patient_id == patient_id)
        .first()
    )
    if medicine is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="medicine_id does not refer to one of your medicines",
        )


def get_owned_health_note(
    note_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> HealthNote:
    note = (
        db.query(HealthNote)
        .filter(HealthNote.id == note_id, HealthNote.patient_id == current_user.patient_profile.id)
        .first()
    )
    if note is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Health note not found")
    return note


@router.post("", response_model=HealthNoteResponse, status_code=status.HTTP_201_CREATED)
def create_health_note(
    note_in: HealthNoteCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> HealthNote:
    patient_id = current_user.patient_profile.id
    _validate_medicine_ownership(note_in.medicine_id, patient_id, db)

    note = HealthNote(
        patient_id=patient_id,
        text=note_in.text,
        recorded_at=note_in.recorded_at or local_now(),
        medicine_id=note_in.medicine_id,
    )
    db.add(note)
    db.commit()
    db.refresh(note)
    return note


@router.get("", response_model=list[HealthNoteResponse])
def list_health_notes(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> list[HealthNote]:
    return (
        db.query(HealthNote)
        .filter(HealthNote.patient_id == current_user.patient_profile.id)
        .order_by(HealthNote.recorded_at.desc())
        .all()
    )


@router.get("/{note_id}", response_model=HealthNoteResponse)
def get_health_note(note: HealthNote = Depends(get_owned_health_note)) -> HealthNote:
    return note


@router.patch("/{note_id}", response_model=HealthNoteResponse)
def update_health_note(
    note_in: HealthNoteUpdate,
    note: HealthNote = Depends(get_owned_health_note),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> HealthNote:
    updates = note_in.model_dump(exclude_unset=True)
    if "medicine_id" in updates:
        _validate_medicine_ownership(updates["medicine_id"], current_user.patient_profile.id, db)

    for field, value in updates.items():
        setattr(note, field, value)

    db.commit()
    db.refresh(note)
    return note


@router.delete("/{note_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_health_note(
    note: HealthNote = Depends(get_owned_health_note), db: Session = Depends(get_db)
) -> None:
    # Real delete, unlike Medicine's soft-delete — a personal note carries
    # no adherence/timeline history that needs preserving. If a patient
    # wants it gone, it should actually be gone.
    db.delete(note)
    db.commit()
