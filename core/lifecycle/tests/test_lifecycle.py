"""lifecycle 모듈 테스트"""

import pytest
from core.lifecycle import LifeCycle


class TestLifeCycle:
    """LifeCycle 기본 동작 테스트"""

    def test_create_lifecycle(self):
        """lifecycle 인스턴스 생성 테스트"""
        lc = LifeCycle.create()
        assert lc is not None
        assert hasattr(lc, "id")
        assert lc.id is not None

    def test_with_lifecycle_decorator(self):
        """with_lifecycle decorator 기본 동작 테스트"""
        result = []

        @LifeCycle.with_lifecycle()
        def test_func():
            lc = LifeCycle.get_lifecycle()
            result.append(lc.id)
            return "success"

        ret = test_func()

        assert ret == "success"
        assert len(result) == 1
        assert result[0] is not None

    def test_get_lifecycle_in_decorated_function(self):
        """decorated 함수 내에서 get_lifecycle() 호출 테스트"""
        captured_id = None

        @LifeCycle.with_lifecycle()
        def test_func():
            nonlocal captured_id
            lc = LifeCycle.get_lifecycle()
            captured_id = lc.id
            return lc

        returned_lc = test_func()

        assert captured_id is not None
        assert returned_lc.id == captured_id

    def test_get_lifecycle_raises_outside_context(self):
        """lifecycle 컨텍스트 밖에서 get_lifecycle() 호출 시 예외 발생 테스트"""
        with pytest.raises(LookupError):
            LifeCycle.get_lifecycle()

    def test_lifecycle_isolation_between_calls(self):
        """함수 호출마다 새로운 lifecycle 인스턴스 생성 테스트"""
        ids = []

        @LifeCycle.with_lifecycle()
        def test_func():
            lc = LifeCycle.get_lifecycle()
            ids.append(lc.id)

        test_func()
        test_func()
        test_func()

        assert len(ids) == 3
        assert len(set(ids)) == 3  # 모두 다른 ID

    def test_lifecycle_cleanup_after_function(self):
        """함수 종료 후 lifecycle이 정리되는지 테스트"""
        @LifeCycle.with_lifecycle()
        def test_func():
            lc = LifeCycle.get_lifecycle()
            return lc.id

        # 함수 실행
        test_func()

        # 함수 종료 후에는 lifecycle이 없어야 함
        with pytest.raises(LookupError):
            LifeCycle.get_lifecycle()

    def test_lifecycle_cleanup_on_exception(self):
        """예외 발생 시에도 lifecycle이 정리되는지 테스트"""
        @LifeCycle.with_lifecycle()
        def test_func():
            lc = LifeCycle.get_lifecycle()
            assert lc is not None
            raise ValueError("test exception")

        # 예외가 발생해도 lifecycle은 정리되어야 함
        with pytest.raises(ValueError):
            test_func()

        # 정리 후에는 lifecycle이 없어야 함
        with pytest.raises(LookupError):
            LifeCycle.get_lifecycle()

    def test_with_lifecycle_custom_factory(self):
        """커스텀 factory를 사용한 lifecycle 생성 테스트"""
        class CustomLifeCycle(LifeCycle):
            custom_field: str = "custom_value"

        @LifeCycle.with_lifecycle(factory=lambda: CustomLifeCycle.create(custom_field="test"))
        def test_func():
            lc = LifeCycle.get_lifecycle()
            return lc

        result = test_func()
        assert isinstance(result, CustomLifeCycle)
        assert result.custom_field == "test"

    def test_nested_lifecycle_contexts(self):
        """중첩된 lifecycle 컨텍스트 테스트"""
        outer_id = None
        inner_id = None

        @LifeCycle.with_lifecycle()
        def outer_func():
            nonlocal outer_id
            outer_id = LifeCycle.get_lifecycle().id

            @LifeCycle.with_lifecycle()
            def inner_func():
                nonlocal inner_id
                inner_id = LifeCycle.get_lifecycle().id

            inner_func()

        outer_func()

        assert outer_id is not None
        assert inner_id is not None
        assert outer_id != inner_id  # 각각 다른 lifecycle

    def test_lifecycle_with_function_arguments(self):
        """함수 인자가 있는 경우 lifecycle 동작 테스트"""
        @LifeCycle.with_lifecycle()
        def test_func(x: int, y: int = 10):
            lc = LifeCycle.get_lifecycle()
            assert lc is not None
            return x + y

        result = test_func(5, y=3)
        assert result == 8

    def test_lifecycle_close_called(self):
        """lifecycle.close()가 호출되는지 테스트"""
        close_called = []

        class TrackableLifeCycle(LifeCycle):
            def close(self):
                close_called.append(self.id)
                super().close()

        @LifeCycle.with_lifecycle(factory=TrackableLifeCycle.create)
        def test_func():
            lc = LifeCycle.get_lifecycle()
            return lc.id

        lifecycle_id = test_func()

        assert len(close_called) == 1
        assert close_called[0] == lifecycle_id
