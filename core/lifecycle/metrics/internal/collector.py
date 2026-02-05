"""LifeCycle 메트릭 수집기

Prometheus 메트릭으로 LifeCycle 실행 정보를 수집한다.
"""
from __future__ import annotations
import time
from prometheus_client import Counter, Histogram, Gauge, REGISTRY


# 메트릭 캐시 (중복 생성 방지)
_metrics_cache: dict[str, Counter | Histogram | Gauge] = {}


def _get_or_create_metric(metric_class, name: str, description: str, labelnames: list[str]):
    """메트릭을 가져오거나 새로 생성

    이미 생성된 메트릭이 있으면 재사용하고, 없으면 새로 생성한다.
    테스트 환경에서 중복 등록을 방지한다.
    """
    # 캐시에서 먼저 확인
    if name in _metrics_cache:
        return _metrics_cache[name]

    # 레지스트리에 이미 등록된 메트릭 찾기
    # Counter는 _total suffix를 자동으로 제거하므로, 이를 고려해야 함
    search_names = [name]
    if metric_class == Counter and name.endswith('_total'):
        # Counter의 실제 이름은 _total이 제거된 형태
        search_names.append(name[:-6])  # '_total' 제거

    for collector in list(REGISTRY._collector_to_names.keys()):
        if hasattr(collector, '_name') and collector._name in search_names:
            _metrics_cache[name] = collector
            return collector

    # 없으면 새로 생성
    try:
        metric = metric_class(name, description, labelnames)
        _metrics_cache[name] = metric
        return metric
    except ValueError as e:
        # 중복 등록 오류 발생 시 레지스트리에서 다시 찾기
        if "Duplicated timeseries" in str(e):
            for collector in list(REGISTRY._collector_to_names.keys()):
                if hasattr(collector, '_name') and collector._name in search_names:
                    _metrics_cache[name] = collector
                    return collector
        raise


# RLife 메트릭
rlife_duration = _get_or_create_metric(
    Histogram,
    "lifecycle_rlife_duration_seconds",
    "RLife 실행 시간",
    ["event", "receiver"]
)

rlife_total = _get_or_create_metric(
    Counter,
    "lifecycle_rlife_total",
    "RLife 호출 횟수",
    ["event", "receiver"]
)

# HLife 메트릭
hlife_duration = _get_or_create_metric(
    Histogram,
    "lifecycle_hlife_duration_seconds",
    "HLife 실행 시간",
    ["handler", "method"]
)

hlife_total = _get_or_create_metric(
    Counter,
    "lifecycle_hlife_total",
    "HLife 호출 횟수",
    ["handler", "method"]
)

# Active gauge
lifecycle_active = _get_or_create_metric(
    Gauge,
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
