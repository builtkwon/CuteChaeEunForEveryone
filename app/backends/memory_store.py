import time
from app.backends.base import ResultData, ResultStore

_TTL_SECONDS = 3600  # 1시간 후 자동 만료


class InMemoryResultStore(ResultStore):
    """메모리 기반 ResultStore 구현체.

    서버 재시작 시 데이터가 초기화됩니다.
    Redis 등 영구 저장소로 교체하려면 RedisResultStore를 구현하세요.
    """

    def __init__(self) -> None:
        self._data: dict[str, tuple[ResultData, float]] = {}

    def save(self, file_id: str, data: ResultData) -> None:
        self._purge_expired()
        self._data[file_id] = (data, time.monotonic())

    def get(self, file_id: str) -> ResultData | None:
        entry = self._data.get(file_id)
        if not entry:
            return None
        data, saved_at = entry
        if time.monotonic() - saved_at > _TTL_SECONDS:
            del self._data[file_id]
            return None
        return data

    def _purge_expired(self) -> None:
        now = time.monotonic()
        expired = [k for k, (_, t) in self._data.items() if now - t > _TTL_SECONDS]
        for k in expired:
            del self._data[k]
