from __future__ import annotations

from typing import Callable

from .lifecycle import LifeCycle

LifecycleSink = Callable[[LifeCycle], None]


class LifecycleSinkRegistry:
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
