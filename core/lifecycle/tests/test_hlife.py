"""HLife 테스트"""

import pytest
from core.lifecycle import HLife, LifeCycle


class TestHLife:
    """HLife 기본 동작 테스트"""

    async def test_hlife_snapshot(self):
        """set_snapshot() 동작 검증"""
        captured_hlife = None

        @LifeCycle.with_async_lifecycle(
            factory=HLife.create_factory("TestHandler", "test_method")
        )
        async def test_func(value):
            nonlocal captured_hlife
            hlife = HLife.get_lifecycle()
            hlife.set_snapshot(before="old", after="new")
            captured_hlife = hlife
            return "done"

        result = await test_func("test")

        assert result == "done"
        assert captured_hlife.before_snapshot == "old"
        assert captured_hlife.after_snapshot == "new"

    async def test_hlife_events(self):
        """add_events() 동작 검증"""
        captured_hlife = None

        @LifeCycle.with_async_lifecycle(
            factory=HLife.create_factory("TestHandler", "test_method")
        )
        async def test_func():
            nonlocal captured_hlife
            hlife = HLife.get_lifecycle()

            mock_events = ["event1", "event2"]
            hlife.add_events(mock_events)
            captured_hlife = hlife
            return "done"

        result = await test_func()

        assert result == "done"
        assert captured_hlife.events == ["event1", "event2"]

    async def test_hlife_auto_capture_args(self):
        """with_async_lifecycle() args 자동 캡처 검증"""
        captured_hlife = None

        class TestClass:
            @classmethod
            @LifeCycle.with_async_lifecycle(
                factory=HLife.create_factory("TestHandler", "test_method")
            )
            async def test_method(cls, arg1, arg2, kwarg1="default"):
                nonlocal captured_hlife
                captured_hlife = HLife.get_lifecycle()
                return "done"

        result = await TestClass.test_method("value1", "value2", kwarg1="custom")

        assert result == "done"
        assert captured_hlife.handler_name == "TestHandler"
        assert captured_hlife.method_name == "test_method"
        # cls 제외한 args와 kwargs 검증
        assert captured_hlife.params.args == ("value1", "value2")
        assert captured_hlife.params.kwargs == {"kwarg1": "custom"}

    async def test_hlife_set_snapshot_partial(self):
        """set_snapshot() before/after 개별 설정 검증"""
        captured_hlife = None

        @LifeCycle.with_async_lifecycle(
            factory=HLife.create_factory("TestHandler", "test_method")
        )
        async def test_func():
            nonlocal captured_hlife
            hlife = HLife.get_lifecycle()

            # before만 설정
            hlife.set_snapshot(before="old_value")
            assert hlife.before_snapshot == "old_value"
            assert hlife.after_snapshot is None

            # after만 설정
            hlife.set_snapshot(after="new_value")
            assert hlife.before_snapshot == "old_value"
            assert hlife.after_snapshot == "new_value"

            captured_hlife = hlife
            return "done"

        await test_func()

        assert captured_hlife.before_snapshot == "old_value"
        assert captured_hlife.after_snapshot == "new_value"
