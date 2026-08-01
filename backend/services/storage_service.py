"""
Storage abstraction. Uses the local filesystem during development and can
be pointed at any S3-compatible bucket (AWS S3, MinIO, DigitalOcean
Spaces...) in production by switching STORAGE_BACKEND=s3 in settings.
"""
from __future__ import annotations

import shutil
import uuid
from pathlib import Path

from fastapi import UploadFile

from config.settings import get_settings

settings = get_settings()


class StorageService:
    def __init__(self) -> None:
        self.backend = settings.STORAGE_BACKEND
        if self.backend == "local":
            self.base_path = Path(settings.LOCAL_STORAGE_PATH)
            self.base_path.mkdir(parents=True, exist_ok=True)

    def _unique_name(self, original_filename: str) -> str:
        suffix = Path(original_filename).suffix
        return f"{uuid.uuid4().hex}{suffix}"

    def save(self, upload: UploadFile, subfolder: str) -> str:
        """Persist an uploaded file and return its storage path/key."""
        filename = self._unique_name(upload.filename or "file")
        if self.backend == "local":
            folder = self.base_path / subfolder
            folder.mkdir(parents=True, exist_ok=True)
            destination = folder / filename
            with destination.open("wb") as f:
                shutil.copyfileobj(upload.file, f)
            return str(destination)

        return self._save_s3(upload, subfolder, filename)

    def _save_s3(self, upload: UploadFile, subfolder: str, filename: str) -> str:
        import boto3  # lazy import: only required when STORAGE_BACKEND=s3

        client = boto3.client(
            "s3",
            region_name=settings.S3_REGION,
            endpoint_url=settings.S3_ENDPOINT_URL or None,
            aws_access_key_id=settings.S3_ACCESS_KEY or None,
            aws_secret_access_key=settings.S3_SECRET_KEY or None,
        )
        key = f"{subfolder}/{filename}"
        client.upload_fileobj(upload.file, settings.S3_BUCKET_NAME, key)
        return f"s3://{settings.S3_BUCKET_NAME}/{key}"

    def resolve_local_path(self, stored_path: str) -> str:
        """For local backend the stored path IS the filesystem path already."""
        return stored_path


storage_service = StorageService()
