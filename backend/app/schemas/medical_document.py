from datetime import date, datetime

from pydantic import BaseModel, ConfigDict

from app.models.medical_document import DocumentType


class MedicalDocumentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    document_type: DocumentType
    original_filename: str
    content_type: str
    document_date: date | None
    description: str | None
    uploaded_at: datetime
    # storage_key deliberately excluded — an internal detail, not something
    # the API exposes. Downloads go through the document's own id.
