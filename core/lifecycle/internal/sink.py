from __future__ import annotations

from typing import Callable

from .lifecycle import LifeCycle

LifecycleSink = Callable[[LifeCycle], None]


class LifecycleSinkRegistry:
    """lifecycle 발생 시점을 구독하는 observer hook 레지스트리.

    hlife/rlife가 stats·log 모듈을 직접 import하면 core lifecycle이 관측 기능에
    의존하게 된다. 의존 방향을 끊으려고 sink를 두고, 관측 측(예: stats recorder)이
    add_lifecycle_sink로 구독해 emit 시점에 이벤트를 받아간다.
    """

    def __init__(self) -> None:
        self._sinks: list[LifecycleSink] = []

    def add(self, sink: LifecycleSink) -> LifecycleSink:
        if sink not in self._sinks:
            self._sinks.append(sink)
        return sink

    def remove(self, sink: LifecycleSink) -> None:
        if sink in self._sinks:
            self._sinks.remove(sink)

    def emit(self, lifecycle: LifeCycle) -> None:
        for sink in list(self._sinks):
            sink(lifecycle)


_sink_registry = LifecycleSinkRegistry()


def add_lifecycle_sink(sink: LifecycleSink) -> LifecycleSink:
    return _sink_registry.add(sink)


def remove_lifecycle_sink(sink: LifecycleSink) -> None:
    _sink_registry.remove(sink)


def emit_lifecycle(lifecycle: LifeCycle) -> None:
    _sink_registry.emit(lifecycle)
