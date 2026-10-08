from tests.conftest import register_and_login
from tests.test_documents import upload


def create_prescription(client, headers, **overrides):
    payload = {"prescription_date": "2026-09-01"}
    payload.update(overrides)
    return client.post("/api/v1/prescriptions", headers=headers, json=payload)


def upload_prescription_document(client, headers, document_type="prescription"):
    return upload(client, headers, document_type=document_type).json()["id"]


def test_create_prescription_manual(client):
    headers = register_and_login(client)

    response = create_prescription(
        client, headers, doctor_name="Dr. Rao", hospital_name="City Clinic", notes="Take after food"
    )

    assert response.status_code == 201
    body = response.json()
    assert body["prescription_date"] == "2026-09-01"
    assert body["doctor_name"] == "Dr. Rao"
    assert body["hospital_name"] == "City Clinic"
    assert body["document_id"] is None
    assert body["source"] == "manual"


def test_create_requires_prescription_date(client):
    headers = register_and_login(client)

    response = client.post("/api/v1/prescriptions", headers=headers, json={"doctor_name": "Dr. Rao"})

    assert response.status_code == 422


def test_create_requires_auth(client):
    response = client.post("/api/v1/prescriptions", json={"prescription_date": "2026-09-01"})

    assert response.status_code == 401


def test_source_cannot_be_set_by_client(client):
    headers = register_and_login(client)

    response = create_prescription(client, headers, source="document_upload")

    assert response.status_code == 201
    assert response.json()["source"] == "manual"


def test_create_with_document_sets_source_to_document_upload(client):
    headers = register_and_login(client)
    document_id = upload_prescription_document(client, headers)

    response = create_prescription(client, headers, document_id=document_id)

    assert response.status_code == 201
    body = response.json()
    assert body["document_id"] == document_id
    assert body["source"] == "document_upload"


def test_create_rejects_document_of_other_patient(client):
    headers_a = register_and_login(client, email="a@example.com")
    headers_b = register_and_login(client, email="b@example.com")
    document_id = upload_prescription_document(client, headers_a)

    response = create_prescription(client, headers_b, document_id=document_id)

    assert response.status_code == 400


def test_create_rejects_document_that_is_not_a_prescription(client):
    headers = register_and_login(client)
    document_id = upload_prescription_document(client, headers, document_type="lab_report")

    response = create_prescription(client, headers, document_id=document_id)

    assert response.status_code == 400


def test_list_is_newest_first_and_scoped_to_patient(client):
    headers_a = register_and_login(client, email="a@example.com")
    headers_b = register_and_login(client, email="b@example.com")
    create_prescription(client, headers_a, prescription_date="2026-01-10")
    create_prescription(client, headers_a, prescription_date="2026-03-05")
    create_prescription(client, headers_b, prescription_date="2026-02-01")

    response = client.get("/api/v1/prescriptions", headers=headers_a)

    assert response.status_code == 200
    assert [p["prescription_date"] for p in response.json()] == ["2026-03-05", "2026-01-10"]


def test_get_prescription(client):
    headers = register_and_login(client)
    prescription_id = create_prescription(client, headers).json()["id"]

    response = client.get(f"/api/v1/prescriptions/{prescription_id}", headers=headers)

    assert response.status_code == 200
    assert response.json()["id"] == prescription_id


def test_cross_patient_access_returns_404(client):
    headers_a = register_and_login(client, email="a@example.com")
    headers_b = register_and_login(client, email="b@example.com")
    prescription_id = create_prescription(client, headers_a).json()["id"]
    url = f"/api/v1/prescriptions/{prescription_id}"

    assert client.get(url, headers=headers_b).status_code == 404
    assert client.patch(url, headers=headers_b, json={"notes": "hijack"}).status_code == 404
    assert client.delete(url, headers=headers_b).status_code == 404
    # still intact for the owner
    assert client.get(url, headers=headers_a).status_code == 200


def test_update_prescription(client):
    headers = register_and_login(client)
    prescription_id = create_prescription(client, headers).json()["id"]

    response = client.patch(
        f"/api/v1/prescriptions/{prescription_id}",
        headers=headers,
        json={"doctor_name": "Dr. Menon", "prescription_date": "2026-09-15"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["doctor_name"] == "Dr. Menon"
    assert body["prescription_date"] == "2026-09-15"


def test_update_cannot_clear_prescription_date(client):
    headers = register_and_login(client)
    prescription_id = create_prescription(client, headers).json()["id"]

    response = client.patch(
        f"/api/v1/prescriptions/{prescription_id}", headers=headers, json={"prescription_date": None}
    )

    assert response.status_code == 422


def test_update_document_recomputes_source(client):
    headers = register_and_login(client)
    prescription_id = create_prescription(client, headers).json()["id"]
    document_id = upload_prescription_document(client, headers)
    url = f"/api/v1/prescriptions/{prescription_id}"

    attached = client.patch(url, headers=headers, json={"document_id": document_id})
    assert attached.status_code == 200
    assert attached.json()["source"] == "document_upload"

    detached = client.patch(url, headers=headers, json={"document_id": None})
    assert detached.status_code == 200
    assert detached.json()["document_id"] is None
    assert detached.json()["source"] == "manual"


def test_update_rejects_document_of_other_patient(client):
    headers_a = register_and_login(client, email="a@example.com")
    headers_b = register_and_login(client, email="b@example.com")
    document_id = upload_prescription_document(client, headers_a)
    prescription_id = create_prescription(client, headers_b).json()["id"]

    response = client.patch(
        f"/api/v1/prescriptions/{prescription_id}", headers=headers_b, json={"document_id": document_id}
    )

    assert response.status_code == 400


def test_delete_prescription_keeps_linked_document(client):
    headers = register_and_login(client)
    document_id = upload_prescription_document(client, headers)
    prescription_id = create_prescription(client, headers, document_id=document_id).json()["id"]

    response = client.delete(f"/api/v1/prescriptions/{prescription_id}", headers=headers)

    assert response.status_code == 204
    assert client.get(f"/api/v1/prescriptions/{prescription_id}", headers=headers).status_code == 404
    assert client.get(f"/api/v1/documents/{document_id}", headers=headers).status_code == 200
