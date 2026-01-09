"""RLife 테스트"""

import pytest
from core.lifecycle import RLife, LifeCycle


class TestRLife:
    """RLife 기본 동작 테스트"""

    async def test_rlife_event_capture(self) -> None:
        """Event 캡처 검증"""
        # Mock event 객체
        class MockEvent:
            def __init__(self, event_name: str, payload: dict[str, str]) -> None:
                self.event_name = event_name
                self.payload = payload

        captured_rlife: RLife | None = None

        @LifeCycle.with_async_lifecycle(factory=RLife.create_factory)
        async def test_receiver(event: MockEvent) -> str:
            nonlocal captured_rlife
            captured_rlife = RLife.get_lifecycle()
            return "done"

        mock_event = MockEvent(event_name="TestEvent", payload={"key": "value", "id": "user123"})
        result = await test_receiver(mock_event)

        assert result == "done"
        assert captured_rlife.receiver_name == "test_receiver"
        assert captured_rlife.event == mock_event
        assert captured_rlife.event.event_name == "TestEvent"
        assert captured_rlife.event.payload == {"key": "value", "id": "user123"}

    async def test_rlife_event_serialization_with_to_dict(self) -> None:
        """to_dict 메서드가 있는 Event 직렬화 검증"""
        # to_dict 메서드가 있는 Event
        class MockEvent:
            def __init__(self, event_name: str, payload: dict[str, object]) -> None:
                self.event_name = event_name
                self.payload = payload

            def to_dict(self) -> dict[str, object]:
                return {
                    "event_name": self.event_name,
                    "payload": self.payload
                }

        captured_rlife: RLife | None = None

        @LifeCycle.with_async_lifecycle(factory=RLife.create_factory)
        async def test_receiver(event: MockEvent) -> str:
            nonlocal captured_rlife
            captured_rlife = RLife.get_lifecycle()
            return "done"

        mock_event = MockEvent(event_name="TestEvent", payload={"id": "user1", "data": {"x": 5}})
        await test_receiver(mock_event)

        # close() 호출 시 직렬화 확인
        assert captured_rlife.event == mock_event
        # Event.to_dict() 메서드 동작 확인
        assert captured_rlife.event.to_dict() == {
            "event_name": "TestEvent",
            "payload": {"id": "user1", "data": {"x": 5}}
        }

    async def test_rlife_event_without_to_dict(self) -> None:
        """to_dict 메서드가 없는 Event는 str() 처리"""
        # to_dict 메서드 없는 간단한 객체
        class SimpleEvent:
            def __init__(self, name: str) -> None:
                self.name = name

            def __str__(self) -> str:
                return f"SimpleEvent({self.name})"

        captured_rlife: RLife | None = None

        @LifeCycle.with_async_lifecycle(factory=RLife.create_factory)
        async def test_receiver(event: SimpleEvent) -> str:
            nonlocal captured_rlife
            captured_rlife = RLife.get_lifecycle()
            return "done"

        mock_event = SimpleEvent(name="test")
        await test_receiver(mock_event)

        assert captured_rlife.event == mock_event
        assert str(captured_rlife.event) == "SimpleEvent(test)"

    async def test_rlife_function_name_auto_capture(self) -> None:
        """함수명 자동 캡처 검증"""
        class MockEvent:
            def __init__(self, event_name: str) -> None:
                self.event_name = event_name
                self.payload = "test"

        captured_rlife: RLife | None = None

        @LifeCycle.with_async_lifecycle(factory=RLife.create_factory)
        async def my_custom_receiver_name(event: MockEvent) -> str:
            nonlocal captured_rlife
            captured_rlife = RLife.get_lifecycle()
            return "done"

        mock_event = MockEvent(event_name="AutoCaptureEvent")
        await my_custom_receiver_name(mock_event)

        # 함수명이 자동으로 캡처되었는지 확인
        assert captured_rlife.receiver_name == "my_custom_receiver_name"
        # Event 통째로 저장되었는지 확인
        assert captured_rlife.event == mock_event
        assert captured_rlife.event.event_name == "AutoCaptureEvent"
