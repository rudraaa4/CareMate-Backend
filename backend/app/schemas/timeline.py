import enum
from datetime import datetime

from pydantic import BaseModel


class TimelineItemType(str, enum.Enum):
    PRESCRIPTION = "prescription"
    DOCUMENT = "document"
    TREATMENT_STARTED = "treatment_started"
    TREATMENT_ENDED = "treatment_ended"
    HEALTH_NOTE = "health_note"
    ADHERENCE_SUMMARY = "adherence_summary"


class TimelineItem(BaseModel):
    """One entry in the care thread. Not a database table: items are built
    on request from the records that already exist (see TimelineService)."""

    type: TimelineItemType
    occurred_at: datetime
    title: str
    description: str | None = None
    # id of the underlying record (prescription, document, note, medicine).
    # None for adherence summaries, which are computed rather than stored.
    reference_id: int | None = None
    # Set when the item has a file the patient can fetch via
    # GET /api/v1/documents/{document_id}/download.
    document_id: int | None = None


class TimelineResponse(BaseModel):
    items: list[TimelineItem]
