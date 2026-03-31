import io
import json
from minio import Minio
from minio.error import S3Error
from storage.base import StorageClient
from config.settings import settings


class MinIOClient(StorageClient):
    def __init__(self):
        self._client = Minio(
            settings.MINIO_ENDPOINT,
            access_key=settings.MINIO_ACCESS_KEY,
            secret_key=settings.MINIO_SECRET_KEY,
            secure=False,
        )
        self._bucket = settings.MINIO_BUCKET
        if not self._client.bucket_exists(self._bucket):
            self._client.make_bucket(self._bucket)

    def put_json(self, key: str, data: dict) -> None:
        payload = json.dumps(data).encode("utf-8")
        self._client.put_object(
            self._bucket,
            key,
            io.BytesIO(payload),
            length=len(payload),
            content_type="application/json",
        )

    def get_json(self, key: str) -> dict:
        response = self._client.get_object(self._bucket, key)
        try:
            return json.loads(response.read().decode("utf-8"))
        finally:
            response.close()
            response.release_conn()

    def put_text(self, key: str, text: str) -> None:
        payload = text.encode("utf-8")
        self._client.put_object(
            self._bucket,
            key,
            io.BytesIO(payload),
            length=len(payload),
            content_type="text/plain",
        )

    def get_text(self, key: str) -> str:
        response = self._client.get_object(self._bucket, key)
        try:
            return response.read().decode("utf-8")
        finally:
            response.close()
            response.release_conn()

    def exists(self, key: str) -> bool:
        try:
            self._client.stat_object(self._bucket, key)
            return True
        except S3Error as e:
            if e.code == "NoSuchKey":
                return False
            raise

    def list_keys(self, prefix: str) -> list[str]:
        objects = self._client.list_objects(self._bucket, prefix=prefix, recursive=True)
        return [obj.object_name for obj in objects]
