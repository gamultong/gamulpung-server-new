from __future__ import annotations

from typing import Any, Callable

LifecycleSink = Callable[[Any], None]

_lifecycle_sinks: list[LifecycleSink] = []


def add_lifecycle_sink(sink: LifecycleSink):
    _lifecycle_sinks.append(sink)
    return sink


def remove_lifecycle_sink(sink: LifecycleSink):
    if sink in _lifecycle_sinks:
        _lifecycle_sinks.remove(sink)


def emit_lifecycle(lifecycle: Any):
    for sink in list(_lifecycle_sinks):
        sink(lifecycle)
