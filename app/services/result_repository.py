from app.backends.base import ResultData, ResultStore


class ResultRepository:
    """결과 파일 조회 전용 서비스.

    쓰기(PhotoService)와 읽기를 분리해 main.py가 저장소에 직접 접근하지 않도록 합니다.
    """

    def __init__(self, store: ResultStore) -> None:
        self._store = store

    def get(self, file_id: str) -> ResultData | None:
        return self._store.get(file_id)

    def get_download_filename(self, file_id: str) -> str | None:
        data = self._store.get(file_id)
        if not data:
            return None
        return f"{data['filename'].rsplit('.', 1)[0]}_qr.jpg"
