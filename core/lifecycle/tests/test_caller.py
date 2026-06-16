"""Caller 테스트"""

from core.lifecycle import Caller, RLife, HLife, LifeCycle


class MockEvent:
    """테스트용 Mock Event"""
    def __init__(self, event_name: str, payload: dict | None = None) -> None:
        self.event_name = event_name
        self.payload = payload or {}


class TestCaller:
    """Caller 기본 동작 테스트"""

    async def test_caller_created_in_rlife(self) -> None:
        """RLife 내에서 Caller 자동 생성 검증"""
        captured_caller: Caller | None = None
        captured_rlife: RLife | None = None

        @LifeCycle.with_async_lifecycle(factory=RLife.create_factory)
        async def test_receiver(event: MockEvent) -> str:
            nonlocal captured_caller, captured_rlife
            captured_caller = Caller.get_current()
            captured_rlife = RLife.get_lifecycle()
            return "done"

        mock_event = MockEvent(event_name="TestEvent")
        await test_receiver(mock_event)

        # Caller가 생성되었는지 확인
        assert captured_caller is not None
        assert captured_caller.rlife_id == captured_rlife.id
        assert captured_caller.triggering_event == mock_event
        assert captured_rlife.caller == captured_caller

    async def test_caller_not_exists_outside_rlife(self) -> None:
        """RLife 외부에서 Caller가 없는지 검증"""
        # RLife 컨텍스트 밖에서는 Caller가 None
        assert Caller.get_current() is None

    async def test_hlife_registered_to_caller(self) -> None:
        """HLife가 Caller에 자동 등록되는지 검증"""
        captured_caller: Caller | None = None
        captured_hlife: HLife | None = None

        @LifeCycle.with_async_lifecycle(
            factory=HLife.create_factory("TestHandler", "test_method")
        )
        async def handler_method() -> str:
            nonlocal captured_hlife
            captured_hlife = HLife.get_lifecycle()
            return "handler done"

        @LifeCycle.with_async_lifecycle(factory=RLife.create_factory)
        async def test_receiver(event: MockEvent) -> str:
            nonlocal captured_caller
            await handler_method()
            captured_caller = Caller.get_current()
            return "done"

        mock_event = MockEvent(event_name="TestEvent")
        await test_receiver(mock_event)

        # HLife가 Caller에 등록되었는지 확인
        assert captured_caller is not None
        assert len(captured_caller.hlives) == 1
        assert captured_caller.hlives[0] == captured_hlife
        assert captured_hlife.caller_id == captured_caller.id

    async def test_multiple_hlives_registered_in_order(self) -> None:
        """여러 HLife가 순서대로 등록되는지 검증"""
        captured_caller: Caller | None = None
        captured_hlives: list[HLife] = []

        @LifeCycle.with_async_lifecycle(
            factory=HLife.create_factory("TestHandler", "method1")
        )
        async def handler_method1() -> str:
            captured_hlives.append(HLife.get_lifecycle())
            return "method1 done"

        @LifeCycle.with_async_lifecycle(
            factory=HLife.create_factory("TestHandler", "method2")
        )
        async def handler_method2() -> str:
            captured_hlives.append(HLife.get_lifecycle())
            return "method2 done"

        @LifeCycle.with_async_lifecycle(factory=RLife.create_factory)
        async def test_receiver(event: MockEvent) -> str:
            nonlocal captured_caller
            await handler_method1()
            await handler_method2()
            captured_caller = Caller.get_current()
            return "done"

        mock_event = MockEvent(event_name="TestEvent")
        await test_receiver(mock_event)

        # 2개의 HLife가 순서대로 등록되었는지 확인
        assert captured_caller is not None
        assert len(captured_caller.hlives) == 2
        assert captured_caller.hlives[0] == captured_hlives[0]
        assert captured_caller.hlives[1] == captured_hlives[1]

    async def test_hlife_without_rlife_has_no_caller(self) -> None:
        """RLife 없이 HLife 호출 시 caller_id가 None인지 검증"""
        captured_hlife: HLife | None = None

        @LifeCycle.with_async_lifecycle(
            factory=HLife.create_factory("TestHandler", "direct_method")
        )
        async def direct_handler() -> str:
            nonlocal captured_hlife
            captured_hlife = HLife.get_lifecycle()
            return "direct done"

        # RLife 없이 직접 호출
        await direct_handler()

        # caller_id가 None인지 확인
        assert captured_hlife is not None
        assert captured_hlife.caller_id is None

    async def test_caller_cleanup_after_rlife(self) -> None:
        """RLife 종료 후 Caller가 정리되는지 검증"""
        @LifeCycle.with_async_lifecycle(factory=RLife.create_factory)
        async def test_receiver(event: MockEvent) -> str:
            # RLife 내에서는 Caller 존재
            assert Caller.get_current() is not None
            return "done"

        mock_event = MockEvent(event_name="TestEvent")
        await test_receiver(mock_event)

        # RLife 종료 후에는 Caller가 없어야 함
        assert Caller.get_current() is None

    async def test_nested_rlife_independent_callers(self) -> None:
        """중첩된 RLife가 독립적인 Caller를 갖는지 검증"""
        outer_caller_id: str | None = None
        inner_caller_id: str | None = None

        @LifeCycle.with_async_lifecycle(factory=RLife.create_factory)
        async def inner_receiver(event: MockEvent) -> str:
            nonlocal inner_caller_id
            inner_caller_id = Caller.get_current().id
            return "inner done"

        @LifeCycle.with_async_lifecycle(factory=RLife.create_factory)
        async def outer_receiver(event: MockEvent) -> str:
            nonlocal outer_caller_id
            outer_caller_id = Caller.get_current().id
            await inner_receiver(MockEvent(event_name="InnerEvent"))
            return "outer done"

        mock_event = MockEvent(event_name="OuterEvent")
        await outer_receiver(mock_event)

        # 각 RLife가 독립적인 Caller를 가짐
        assert outer_caller_id is not None
        assert inner_caller_id is not None
        assert outer_caller_id != inner_caller_id
