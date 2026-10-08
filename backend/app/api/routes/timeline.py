from typing import Literal

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.schemas.timeline import TimelineResponse
from app.services.timeline_service import TimelineService

router = APIRouter(prefix="/api/v1/timeline", tags=["Timeline"])


@router.get("", response_model=TimelineResponse)
def get_timeline(
    order: Literal["desc", "asc"] = Query(
        default="desc", description="desc = newest first, asc = oldest first"
    ),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> TimelineResponse:
    items = TimelineService(db, current_user.patient_profile.id).get_timeline(
        newest_first=order == "desc"
    )
    return TimelineResponse(items=items)
