"""Lifecycle Profiler 구현

Lifecycle 실행을 시계열 데이터로 수집하고 Chrome Trace 형식으로 출력한다.
"""
from __future__ import annotations
from typing import Any
import time
import json
import threading


class ProfileRecord:
    """개별 Lifecycle 실행 기록"""

    def __init__(
        self,
        name: str,
        category: str,
        phase: str,
        timestamp: float,
        args: dict[str, Any] | None = None
    ):
        self.name = name
        self.category = category
        self.phase = phase  # "B" (begin), "E" (end)
        self.timestamp = timestamp  # 마이크로초
        self.args = args or {}

    def to_trace_event(self, pid: int = 1, tid: int = 1) -> dict[str, Any]:
        """Chrome Trace 형식으로 변환"""
        event = {
            "name": self.name,
            "cat": self.category,
            "ph": self.phase,
            "ts": self.timestamp,
            "pid": pid,
            "tid": tid,
        }
        if self.args:
            event["args"] = self.args
        return event


# 전역 Profiler 인스턴스 (스레드 간 공유)
_current_profiler: LifecycleProfiler | None = None
_profiler_lock = threading.Lock()


class LifecycleProfiler:
    """Lifecycle 실행을 시계열로 수집하는 Profiler

    Context manager로 사용하여 특정 구간의 Lifecycle을 프로파일링한다.

    사용 예시:
        with LifecycleProfiler() as profiler:
            # 시나리오 실행
            ...

        profiler.save("result.json")
    """

    def __init__(self):
        self._records: list[ProfileRecord] = []
        self._start_time: float = 0
        self._lock = threading.Lock()

    def __enter__(self) -> LifecycleProfiler:
        global _current_profiler
        self._start_time = time.perf_counter()
        with _profiler_lock:
            _current_profiler = self
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        global _current_profiler
        with _profiler_lock:
            _current_profiler = None
        return False

    @classmethod
    def get_current(cls) -> LifecycleProfiler | None:
        """현재 활성화된 Profiler 조회"""
        return _current_profiler

    @classmethod
    def is_enabled(cls) -> bool:
        """Profiler 활성화 여부"""
        return _current_profiler is not None

    def _get_timestamp(self) -> float:
        """시작 시점 기준 마이크로초 타임스탬프"""
        return (time.perf_counter() - self._start_time) * 1_000_000

    def record_begin(
        self,
        name: str,
        category: str,
        args: dict[str, Any] | None = None
    ):
        """Lifecycle 시작 기록"""
        record = ProfileRecord(
            name=name,
            category=category,
            phase="B",
            timestamp=self._get_timestamp(),
            args=args
        )
        with self._lock:
            self._records.append(record)

    def record_end(
        self,
        name: str,
        category: str,
        args: dict[str, Any] | None = None
    ):
        """Lifecycle 종료 기록"""
        record = ProfileRecord(
            name=name,
            category=category,
            phase="E",
            timestamp=self._get_timestamp(),
            args=args
        )
        with self._lock:
            self._records.append(record)

    def to_trace_events(self) -> list[dict[str, Any]]:
        """Chrome Trace 형식 이벤트 목록 반환"""
        return [r.to_trace_event() for r in self._records]

    def to_json(self, indent: int | None = 2) -> str:
        """Chrome Trace JSON 문자열 반환"""
        return json.dumps(self.to_trace_events(), indent=indent)

    def save(self, path: str):
        """Chrome Trace JSON 파일 저장

        저장된 파일은 chrome://tracing 에서 열어 시각화할 수 있다.
        """
        with open(path, "w", encoding="utf-8") as f:
            f.write(self.to_json())

    @property
    def records(self) -> list[ProfileRecord]:
        """기록된 ProfileRecord 목록"""
        return self._records.copy()

    def clear(self):
        """기록 초기화"""
        self._records.clear()
