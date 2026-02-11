"""전역 테스트 설정

모든 테스트에 공통으로 적용되는 fixture를 정의한다.
"""
import pytest
from prometheus_client import REGISTRY


@pytest.fixture(autouse=True)
def cleanup_prometheus():
    """테스트 전후 Prometheus 메트릭 정리

    메트릭이 중복 등록되는 것을 방지한다.
    """
    # 테스트 전 lifecycle 관련 메트릭 정리
    collectors_to_unregister = []
    for collector in list(REGISTRY._collector_to_names.keys()):
        if hasattr(collector, '_name') and collector._name.startswith('lifecycle_'):
            collectors_to_unregister.append(collector)

    for collector in collectors_to_unregister:
        try:
            REGISTRY.unregister(collector)
        except Exception:
            pass

    yield

    # 테스트 후 정리
    collectors_to_unregister = []
    for collector in list(REGISTRY._collector_to_names.keys()):
        if hasattr(collector, '_name') and collector._name.startswith('lifecycle_'):
            collectors_to_unregister.append(collector)

    for collector in collectors_to_unregister:
        try:
            REGISTRY.unregister(collector)
        except Exception:
            pass
