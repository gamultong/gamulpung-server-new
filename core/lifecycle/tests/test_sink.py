"""lifecycle sink 테스트"""

from core.lifecycle import LifeCycle
from core.lifecycle.internal.sink import LifecycleSinkRegistry


class TestLifecycleSinkRegistry:
    def test_add_ignores_duplicate_sink(self) -> None:
        registry = LifecycleSinkRegistry()
        lifecycle = LifeCycle.create()
        emitted: list[str] = []

        def sink(lifecycle: LifeCycle) -> None:
            emitted.append(lifecycle.id)

        registry.add(sink)
        registry.add(sink)

        registry.emit(lifecycle)

        assert emitted == [lifecycle.id]

    def test_remove_sink(self) -> None:
        registry = LifecycleSinkRegistry()
        lifecycle = LifeCycle.create()
        emitted: list[str] = []

        def sink(lifecycle: LifeCycle) -> None:
            emitted.append(lifecycle.id)

        registry.add(sink)
        registry.remove(sink)

        registry.emit(lifecycle)

        assert emitted == []
