"""Remote storage backend for envoy-cli.

Provides an abstract base class and an S3-compatible implementation
for pushing and pulling encrypted .env files to/from remote storage.
"""

from __future__ import annotations

import abc
import io
import logging
import os
from typing import List, Optional

logger = logging.getLogger(__name__)


class RemoteBackend(abc.ABC):
    """Abstract interface for remote storage backends."""

    @abc.abstractmethod
    def upload(self, key: str, data: bytes) -> None:
        """Upload *data* to the remote location identified by *key*."""

    @abc.abstractmethod
    def download(self, key: str) -> bytes:
        """Download and return the raw bytes stored at *key*.

        Raises:
            KeyError: if *key* does not exist on the remote.
        """

    @abc.abstractmethod
    def delete(self, key: str) -> None:
        """Delete the object at *key* from the remote.

        Raises:
            KeyError: if *key* does not exist on the remote.
        """

    @abc.abstractmethod
    def list_keys(self, prefix: str = "") -> List[str]:
        """Return all keys that start with *prefix*."""


class S3Backend(RemoteBackend):
    """S3-compatible remote backend (works with AWS S3, MinIO, R2, etc.).

    Credentials are resolved in the standard boto3 order:
    environment variables → ~/.aws/credentials → IAM role.

    Args:
        bucket:     Name of the S3 bucket to use.
        prefix:     Optional key prefix applied to every object (acts as a
                    namespace so multiple teams can share one bucket).
        endpoint_url: Override the default AWS endpoint (useful for MinIO /
                      Cloudflare R2).
        region_name:  AWS region; falls back to ``AWS_DEFAULT_REGION`` env var.
    """

    def __init__(
        self,
        bucket: str,
        prefix: str = "envoy/",
        endpoint_url: Optional[str] = None,
        region_name: Optional[str] = None,
    ) -> None:
        try:
            import boto3  # type: ignore
        except ImportError as exc:  # pragma: no cover
            raise ImportError(
                "boto3 is required for S3 remote storage. "
                "Install it with: pip install envoy-cli[s3]"
            ) from exc

        self.bucket = bucket
        self.prefix = prefix.rstrip("/") + "/" if prefix else ""

        self._s3 = boto3.client(
            "s3",
            endpoint_url=endpoint_url or os.environ.get("ENVOY_S3_ENDPOINT"),
            region_name=region_name or os.environ.get("AWS_DEFAULT_REGION"),
        )
        logger.debug("S3Backend initialised (bucket=%s, prefix=%s)", bucket, self.prefix)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _full_key(self, key: str) -> str:
        """Return the fully-qualified S3 object key."""
        return f"{self.prefix}{key}"

    # ------------------------------------------------------------------
    # RemoteBackend interface
    # ------------------------------------------------------------------

    def upload(self, key: str, data: bytes) -> None:
        full = self._full_key(key)
        logger.debug("Uploading %d bytes → s3://%s/%s", len(data), self.bucket, full)
        self._s3.upload_fileobj(io.BytesIO(data), self.bucket, full)

    def download(self, key: str) -> bytes:
        import botocore.exceptions  # type: ignore

        full = self._full_key(key)
        buf = io.BytesIO()
        try:
            self._s3.download_fileobj(self.bucket, full, buf)
        except botocore.exceptions.ClientError as exc:
            code = exc.response["Error"]["Code"]
            if code in ("NoSuchKey", "404"):
                raise KeyError(f"Remote key not found: {key!r}") from exc
            raise
        logger.debug("Downloaded %d bytes ← s3://%s/%s", buf.tell(), self.bucket, full)
        return buf.getvalue()

    def delete(self, key: str) -> None:
        import botocore.exceptions  # type: ignore

        full = self._full_key(key)
        try:
            self._s3.delete_object(Bucket=self.bucket, Key=full)
        except botocore.exceptions.ClientError as exc:
            code = exc.response["Error"]["Code"]
            if code in ("NoSuchKey", "404"):
                raise KeyError(f"Remote key not found: {key!r}") from exc
            raise
        logger.debug("Deleted s3://%s/%s", self.bucket, full)

    def list_keys(self, prefix: str = "") -> List[str]:
        full_prefix = self._full_key(prefix)
        paginator = self._s3.get_paginator("list_objects_v2")
        keys: List[str] = []
        for page in paginator.paginate(Bucket=self.bucket, Prefix=full_prefix):
            for obj in page.get("Contents", []):
                # Strip the backend prefix so callers see logical keys only.
                logical = obj["Key"][len(self.prefix):]
                keys.append(logical)
        logger.debug("Listed %d keys under prefix %r", len(keys), prefix)
        return keys
