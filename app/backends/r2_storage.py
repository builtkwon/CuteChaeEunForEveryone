import re
import uuid
import boto3
from botocore.config import Config

from app.backends.base import CloudStorage

_SAFE_EXT = {".jpg", ".jpeg", ".png", ".webp", ".heic"}


def _safe_key(filename: str) -> str:
    """원본 파일명에서 안전한 R2 key를 생성합니다.

    경로 조작 문자와 특수문자를 제거하고 확장자만 보존합니다.
    """
    name = filename.rsplit(".", 1)
    ext  = f".{name[1].lower()}" if len(name) == 2 else ".jpg"
    if ext not in _SAFE_EXT:
        ext = ".jpg"
    return f"{uuid.uuid4()}{ext}"


class CloudflareR2Storage(CloudStorage):
    """Cloudflare R2 기반 CloudStorage 구현체.

    S3 호환 API를 사용하므로 AWS S3로 교체 시에도 이 클래스만 수정하면 됩니다.
    """

    def __init__(
        self,
        account_id: str,
        access_key_id: str,
        secret_access_key: str,
        bucket_name: str,
        public_url: str,
    ) -> None:
        self._client = boto3.client(
            "s3",
            endpoint_url=f"https://{account_id}.r2.cloudflarestorage.com",
            aws_access_key_id=access_key_id,
            aws_secret_access_key=secret_access_key,
            config=Config(signature_version="s3v4"),
            region_name="auto",
        )
        self._bucket     = bucket_name
        self._public_url = public_url.rstrip("/")

    def upload(self, file_bytes: bytes, filename: str) -> str:
        key = _safe_key(filename)
        self._client.put_object(
            Bucket=self._bucket,
            Key=key,
            Body=file_bytes,
            ContentType="image/jpeg",
        )
        return f"{self._public_url}/{key}"
