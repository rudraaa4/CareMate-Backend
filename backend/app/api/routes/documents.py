import io
from collections.abc import Generator
from datetime import date
from typing import BinaryIO
from uuid import uuid4

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.core.config import settings
from app.core.database import get_db
from app.models.medical_document import DocumentType, MedicalDocument
from app.models.user import User
from app.schemas.medical_document import MedicalDocumentResponse
from app.storage.base import FileStorage
from app.storage.local import LocalFileStorage

router = APIRouter(prefix="/api/v1/documents", tags=["Medical Documents"])

# Declared content type -> the only extension we'll ever write for it.
# Whichever extension the client's filename claims is ignored entirely —
# this mapping is the sole source of the stored file's extension.
ALLOWED_CONTENT_TYPES: dict[str, str] = {
    "application/pdf": ".pdf",
    "image/jpeg": ".jpg",
    "image/png": ".png",
}


def get_storage() -> FileStorage:
    """A dependency, not a hardcoded instantiation, specifically so tests
    can override it with a temp-directory-backed storage — the same
    principle as get_db being overridden for the test database (Phase 3).
    Without this, tests would write real files into backend/uploads/."""
    return LocalFileStorage()


async def _read_with_size_limit(file: UploadFile, max_bytes: int) -> bytes:
    chunks = []
    total = 0
    while chunk := await file.read(1024 * 1024):
        total += len(chunk)
        if total > max_bytes:
            raise HTTPException(
                status_code=status.HTTP_413_CONTENT_TOO_LARGE,
                detail=f"File exceeds the {max_bytes} byte upload limit",
            )
        chunks.append(chunk)
    return b"".join(chunks)


def get_owned_document(
    document_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> MedicalDocument:
    document = (
        db.query(MedicalDocument)
        .filter(
            MedicalDocument.id == document_id,
            MedicalDocument.patient_id == current_user.patient_profile.id,
        )
        .first()
    )
    if document is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    return document


@router.post("", response_model=MedicalDocumentResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(...),
    document_type: DocumentType = Form(...),
    document_date: date | None = Form(None),
    description: str | None = Form(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    storage: FileStorage = Depends(get_storage),
) -> MedicalDocument:
    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Unsupported content type: {file.content_type}. "
            f"Allowed: {', '.join(ALLOWED_CONTENT_TYPES)}",
        )

    contents = await _read_with_size_limit(file, settings.max_upload_size_bytes)

    # Server-generated — the client's filename/extension is never used to
    # build this. This, not any filename sanitization, is what actually
    # rules out path traversal.
    storage_key = f"{uuid4().hex}{ALLOWED_CONTENT_TYPES[file.content_type]}"
    storage.save(storage_key, io.BytesIO(contents))

    document = MedicalDocument(
        patient_id=current_user.patient_profile.id,
        document_type=document_type,
        storage_key=storage_key,
        original_filename=file.filename or "upload",
        content_type=file.content_type,
        document_date=document_date,
        description=description,
    )
    db.add(document)
    db.commit()
    db.refresh(document)
    return document


@router.get("", response_model=list[MedicalDocumentResponse])
def list_documents(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> list[MedicalDocument]:
    return (
        db.query(MedicalDocument)
        .filter(MedicalDocument.patient_id == current_user.patient_profile.id)
        .order_by(MedicalDocument.uploaded_at.desc())
        .all()
    )


@router.get("/{document_id}", response_model=MedicalDocumentResponse)
def get_document(document: MedicalDocument = Depends(get_owned_document)) -> MedicalDocument:
    return document


def _stream_file(file_obj: BinaryIO) -> Generator[bytes, None, None]:
    try:
        while chunk := file_obj.read(1024 * 1024):
            yield chunk
    finally:
        file_obj.close()


@router.get("/{document_id}/download")
def download_document(
    document: MedicalDocument = Depends(get_owned_document),
    storage: FileStorage = Depends(get_storage),
) -> StreamingResponse:
    file_obj = storage.open(document.storage_key)
    return StreamingResponse(
        _stream_file(file_obj),
        media_type=document.content_type,
        headers={"Content-Disposition": f'attachment; filename="{document.original_filename}"'},
    )
