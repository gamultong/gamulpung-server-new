"""LifeCycle 메트릭 수집기

Prometheus 메트릭으로 LifeCycle 실행 정보를 수집한다.
"""
from __future__ import annotations
import time
from prometheus_client import Counter, Histogram, Gauge


# RLife 메트릭
rlife_duration = Histogram(
    "lifecycle_rlife_duration_seconds",
    "RLife 실행 시간",
    ["event", "receiver"]
)

rlife_total = Counter(
    "lifecycle_rlife_total",
    "RLife 호출 횟수",
    ["event", "receiver"]
)

# HLife 메트릭
hlife_duration = Histogram(
    "lifecycle_hlife_duration_seconds",
    "HLife 실행 시간",
    ["handler", "method"]
)

hlife_total = Counter(
    "lifecycle_hlife_total",
    "HLife 호출 횟수",
    ["handler", "method"]
)

# Active gauge
lifecycle_active = Gauge(
    "lifecycle_active",
    "현재 실행 중인 LifeCycle 수",
    ["type"]
)


class LifecycleMetrics:
    """LifeCycle 메트릭 수집 헬퍼

    RLife/HLife의 on_enter/on_exit에서 호출하여 메트릭을 수집한다.
    """

    @staticmethod
    def get_event_label(event) -> str:
        """Event에서 라벨 문자열 추출

        Args:
            event: Event 객체 (event_name 속성 필요)

        Returns:
            scope.event_name 형식의 문자열
        """
        if event is None:
            return "unknown"

        event_name = getattr(event, "event_name", None)
        if event_name is None:
            return "unknown"

        scope = getattr(event_name, "get_scope", lambda: "")()
        name = str(event_name)

        if scope:
            return f"{scope}.{name}"
        return name

    @staticmethod
    def rlife_started(receiver: str):
        """RLife 시작 기록

        Args:
            receiver: Receiver 함수명
        """
        lifecycle_active.labels(type="RLife").inc()

    @staticmethod
    def rlife_finished(event, receiver: str, duration: float):
        """RLife 종료 기록

        Args:
            event: Event 객체
            receiver: Receiver 함수명
            duration: 실행 시간 (초)
        """
        event_label = LifecycleMetrics.get_event_label(event)

        rlife_duration.labels(event=event_label, receiver=receiver).observe(duration)
        rlife_total.labels(event=event_label, receiver=receiver).inc()
        lifecycle_active.labels(type="RLife").dec()

    @staticmethod
    def hlife_started(handler: str, method: str):
        """HLife 시작 기록

        Args:
            handler: Handler 클래스명
            method: 메서드명
        """
        lifecycle_active.labels(type="HLife").inc()

    @staticmethod
    def hlife_finished(handler: str, method: str, duration: float):
        """HLife 종료 기록

        Args:
            handler: Handler 클래스명
            method: 메서드명
            duration: 실행 시간 (초)
        """
        hlife_duration.labels(handler=handler, method=method).observe(duration)
        hlife_total.labels(handler=handler, method=method).inc()
        lifecycle_active.labels(type="HLife").dec()

    @staticmethod
    def start_timer() -> float:
        """타이머 시작

        Returns:
            시작 시간 (perf_counter)
        """
        return time.perf_counter()

    @staticmethod
    def get_duration(start_time: float) -> float:
        """경과 시간 계산

        Args:
            start_time: 시작 시간 (perf_counter)

        Returns:
            경과 시간 (초)
        """
        return time.perf_counter() - start_time
