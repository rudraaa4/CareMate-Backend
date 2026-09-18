from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.core.database import get_db
from app.models.patient_profile import PatientProfile
from app.models.user import User
from app.schemas.patient_profile import PatientProfileResponse, PatientProfileUpdate

router = APIRouter(prefix="/api/v1/profile", tags=["Patient Profile"])


@router.get("", response_model=PatientProfileResponse)
def read_my_profile(current_user: User = Depends(get_current_user)) -> PatientProfile:
    # No profile ID in the URL — "my profile" is derived entirely from the
    # JWT via get_current_user, so there's no ID a client could swap out to
    # reach someone else's profile.
    return current_user.patient_profile


@router.patch("", response_model=PatientProfileResponse)
def update_my_profile(
    profile_in: PatientProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> PatientProfile:
    profile = current_user.patient_profile

    # exclude_unset=True: only fields actually present in the request body
    # are applied. Sending {"full_name": "..."} alone leaves phone/DOB
    # untouched, instead of resetting them to null.
    updates = profile_in.model_dump(exclude_unset=True)
    for field, value in updates.items():
        setattr(profile, field, value)

    db.commit()
    db.refresh(profile)
    return profile
