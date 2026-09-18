import io

from app.core.config import settings
from tests.conftest import register_and_login


def upload(client, headers, *, filename="report.pdf", content=b"%PDF-1.4 fake pdf content", content_type="application/pdf", document_type="lab_report", **extra_data):
    data = {"document_type": document_type, **extra_data}
    files = {"file": (filename, io.BytesIO(content), content_type)}
    return client.post("/api/v1/documents", headers=headers, files=files, data=data)


def test_upload_document_success(client):
    headers = register_and_login(client)

    response = upload(client, headers)

    assert response.status_code == 201
    body = response.json()
    assert body["document_type"] == "lab_report"
    assert body["original_filename"] == "report.pdf"
    assert body["content_type"] == "application/pdf"
    assert "storage_key" not in body  # internal detail, never exposed


def test_upload_rejects_disallowed_content_type(client):
    headers = register_and_login(client)

    response = upload(
        client, headers, filename="script.exe", content=b"MZ...", content_type="application/x-msdownload"
    )

    assert response.status_code == 415


def test_upload_rejects_oversized_file(client):
    headers = register_and_login(client)
    oversized = b"x" * (settings.max_upload_size_bytes + 1)

    response = upload(client, headers, content=oversized)

    assert response.status_code == 413


def test_list_documents(client):
    headers = register_and_login(client)
    upload(client, headers, filename="a.pdf")
    upload(client, headers, filename="b.pdf")

    response = client.get("/api/v1/documents", headers=headers)

    assert response.status_code == 200
    assert len(response.json()) == 2


def test_get_document_metadata(client):
    headers = register_and_login(client)
    doc_id = upload(client, headers).json()["id"]

    response = client.get(f"/api/v1/documents/{doc_id}", headers=headers)

    assert response.status_code == 200
    assert response.json()["id"] == doc_id


def test_download_document_returns_correct_bytes_and_content_type(client):
    headers = register_and_login(client)
    original_bytes = b"%PDF-1.4 the actual file content"
    doc_id = upload(client, headers, content=original_bytes).json()["id"]

    response = client.get(f"/api/v1/documents/{doc_id}/download", headers=headers)

    assert response.status_code == 200
    assert response.content == original_bytes
    assert response.headers["content-type"] == "application/pdf"
    assert "report.pdf" in response.headers["content-disposition"]


def test_malicious_filename_never_escapes_upload_directory(client):
    """The original filename is stored only as display metadata — the
    actual storage_key is always server-generated. Confirm a
    path-traversal-shaped filename doesn't do anything unusual: the
    document uploads and downloads correctly, and its stored filename
    metadata is preserved as inert text, never interpreted as a path."""
    headers = register_and_login(client)
    evil_name = "../../../../etc/passwd"

    response = upload(client, headers, filename=evil_name, content=b"%PDF-1.4 x")

    assert response.status_code == 201
    doc_id = response.json()["id"]
    assert response.json()["original_filename"] == evil_name  # stored verbatim as metadata, harmlessly

    download = client.get(f"/api/v1/documents/{doc_id}/download", headers=headers)
    assert download.status_code == 200
    assert download.content == b"%PDF-1.4 x"


def test_patient_a_cannot_access_patient_bs_document(client):
    headers_a = register_and_login(client, email="a@example.com")
    headers_b = register_and_login(client, email="b@example.com")
    doc_id = upload(client, headers_a).json()["id"]

    get_response = client.get(f"/api/v1/documents/{doc_id}", headers=headers_b)
    download_response = client.get(f"/api/v1/documents/{doc_id}/download", headers=headers_b)

    assert get_response.status_code == 404
    assert download_response.status_code == 404


def test_documents_require_auth(client):
    assert client.get("/api/v1/documents").status_code == 401


def test_uploads_are_never_served_as_static_files(client):
    """Confirms there's no StaticFiles mount exposing backend/uploads/
    directly — the only way to get file bytes is the authenticated,
    ownership-checked /download route."""
    response = client.get("/uploads/anything.pdf")
    assert response.status_code == 404
