from io import BytesIO

from minio import Minio
from minio.error import MinioException

from app.core.config import get_settings


class ObjectStorageError(RuntimeError):
    pass


class MinioStorageService:
    def __init__(self) -> None:
        settings = get_settings()
        self.bucket = settings.minio_bucket
        self.client = Minio(
            settings.minio_endpoint,
            access_key=settings.minio_access_key,
            secret_key=settings.minio_secret_key,
            secure=settings.minio_secure,
        )

    def upload_bytes(self, object_key: str, content: bytes, content_type: str | None = None) -> None:
        try:
            self._ensure_bucket()
            self.client.put_object(
                self.bucket,
                object_key,
                BytesIO(content),
                length=len(content),
                content_type=content_type or "application/octet-stream",
            )
        except MinioException as exc:
            raise ObjectStorageError(f"MinIO upload failed: {exc}") from exc

    def download_bytes(self, object_key: str) -> bytes:
        try:
            response = self.client.get_object(self.bucket, object_key)
            try:
                return response.read()
            finally:
                response.close()
                response.release_conn()
        except MinioException as exc:
            raise ObjectStorageError(f"MinIO download failed: {exc}") from exc

    def _ensure_bucket(self) -> None:
        if not self.client.bucket_exists(self.bucket):
            self.client.make_bucket(self.bucket)
