from typing import BinaryIO

import boto3

from app.storage.base import FileStorage


class S3FileStorage(FileStorage):
    """Stores documents as private objects in an S3 bucket.

    No credentials are configured here on purpose: boto3 finds them itself
    (an IAM role attached to the EC2 instance in AWS, or the developer's own
    `aws configure` profile locally), so no access key ever sits in the code,
    the image, or .env. The bucket stays private; files only leave through
    the authenticated, ownership-checked download route.
    """

    def __init__(self, bucket: str, region: str | None = None, client=None):
        self.bucket = bucket
        self._client = client or boto3.client("s3", region_name=region)

    def save(self, storage_key: str, file: BinaryIO) -> None:
        self._client.upload_fileobj(
            file,
            self.bucket,
            storage_key,
            ExtraArgs={"ServerSideEncryption": "AES256"},
        )

    def open(self, storage_key: str) -> BinaryIO:
        # The response body is a streaming file-like object (read/close),
        # which is all the download route needs.
        return self._client.get_object(Bucket=self.bucket, Key=storage_key)["Body"]

    def delete(self, storage_key: str) -> None:
        self._client.delete_object(Bucket=self.bucket, Key=storage_key)
