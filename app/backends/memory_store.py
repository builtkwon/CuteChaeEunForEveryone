from app.backends.base import ResultStore


class InMemoryResultStore(ResultStore):
    """메모리 기반 ResultStore 구현체.

    서버 재시작 시 데이터가 초기화됩니다.
    Redis 등 영구 저장소로 교체하려면 RedisResultStore를 구현하세요.
    """

    def __init__(self):
        self._data: dict[str, dict] = {}

    def save(self, file_id: str, data: dict) -> None:
        self._data[file_id] = data

    def get(self, file_id: str) -> dict | None:
        return self._data.get(file_id)
