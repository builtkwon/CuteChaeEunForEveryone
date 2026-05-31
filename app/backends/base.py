from abc import ABC, abstractmethod


class CloudStorage(ABC):
    """원본 사진을 영구 저장하고 공개 다운로드 URL을 반환하는 인터페이스.

    Google Drive → S3 → Cloudflare R2 등으로 교체 시 이 클래스만 구현하면 됩니다.
    """

    @abstractmethod
    def upload(self, file_bytes: bytes, filename: str) -> str:
        """파일을 업로드하고 누구나 접근 가능한 다운로드 URL을 반환합니다."""
        ...


class ResultStore(ABC):
    """처리된 결과 파일을 임시 보관하는 인터페이스.

    In-memory → Redis → S3 등으로 교체 시 이 클래스만 구현하면 됩니다.
    """

    @abstractmethod
    def save(self, file_id: str, data: dict) -> None: ...

    @abstractmethod
    def get(self, file_id: str) -> dict | None: ...
