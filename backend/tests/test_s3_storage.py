import io

import pytest

from app.api.routes import documents
from app.core.config import settings
from app.storage.local import LocalFileStorage
from app.storage.s3 import S3FileStorage


class FakeS3Client:
    """In-memory stand-in for boto3's S3 client: records the calls the
    storage class makes, so tests need no AWS account or network."""

    def __init__(self):
        self.objects: dict[tuple[str, str], bytes] = {}
        self.extra_args: dict[tuple[str, str], dict] = {}

    def upload_fileobj(self, file, bucket, key, ExtraArgs=None):
        self.objects[(bucket, key)] = file.read()
        self.extra_args[(bucket, key)] = ExtraArgs or {}

    def get_object(self, Bucket, Key):
        return {"Body": io.BytesIO(self.objects[(Bucket, Key)])}

    def delete_object(self, Bucket, Key):
        self.objects.pop((Bucket, Key), None)


def test_save_open_delete_roundtrip():
    client = FakeS3Client()
    storage = S3FileStorage("caremate-docs", client=client)

    storage.save("abc.pdf", io.BytesIO(b"%PDF-1.4 data"))
    assert storage.open("abc.pdf").read() == b"%PDF-1.4 data"

    storage.delete("abc.pdf")
    assert ("caremate-docs", "abc.pdf") not in client.objects


def test_objects_are_encrypted_at_rest():
    client = FakeS3Client()
    S3FileStorage("caremate-docs", client=client).save("abc.pdf", io.BytesIO(b"x"))

    assert client.extra_args[("caremate-docs", "abc.pdf")] == {"ServerSideEncryption": "AES256"}


def test_delete_missing_key_is_not_an_error():
    S3FileStorage("caremate-docs", client=FakeS3Client()).delete("never-existed.pdf")


def test_get_storage_defaults_to_local(monkeypatch):
    monkeypatch.setattr(settings, "storage_backend", "local")

    assert isinstance(documents.get_storage(), LocalFileStorage)


def test_get_storage_uses_s3_when_configured(monkeypatch):
    monkeypatch.setattr(settings, "storage_backend", "s3")
    monkeypatch.setattr(settings, "s3_bucket", "caremate-docs")
    monkeypatch.setattr(settings, "aws_region", "ap-south-1")
    documents._s3_storage.cache_clear()

    storage = documents.get_storage()

    assert isinstance(storage, S3FileStorage)
    assert storage.bucket == "caremate-docs"
    documents._s3_storage.cache_clear()


def test_s3_backend_without_bucket_fails_loudly(monkeypatch):
    monkeypatch.setattr(settings, "storage_backend", "s3")
    monkeypatch.setattr(settings, "s3_bucket", None)
    documents._s3_storage.cache_clear()

    with pytest.raises(RuntimeError, match="S3_BUCKET"):
        documents.get_storage()
