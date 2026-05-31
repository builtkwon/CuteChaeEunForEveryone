import uuid
from pathlib import Path

from app.backends.base import CloudStorage, ResultStore
from app.qr_composer import compose


class PhotoService:
    """업로드 → QR 합성 → 결과 저장 파이프라인 오케스트레이터.

    CloudStorage와 ResultStore에만 의존하므로
    구현체를 교체해도 이 클래스는 변경 없이 동작합니다.
    """

    def __init__(self, storage: CloudStorage, store: ResultStore):
        self._storage = storage
        self._store = store

    def process(self, file_bytes: bytes, filename: str, qr_position: str) -> str:
        """사진을 처리하고 결과를 조회할 수 있는 file_id를 반환합니다."""
        download_url = self._storage.upload(file_bytes, filename)
        result_bytes = compose(file_bytes, download_url, qr_position)

        file_id = str(uuid.uuid4())
        self._store.save(file_id, {
            "filename": filename,
            "data": result_bytes,
            "drive_url": download_url,
            "file_size": f"{len(result_bytes) / 1024:.0f} KB",
            "qr_position": qr_position,
        })
        return file_id

    def get_result(self, file_id: str) -> dict | None:
        return self._store.get(file_id)

    def get_result_filename(self, file_id: str) -> str | None:
        info = self._store.get(file_id)
        if not info:
            return None
        return f"{Path(info['filename']).stem}_qr.jpg"
