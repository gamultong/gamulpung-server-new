from __future__ import annotations
from .lifecycle import LifeCycle, _lifecycle_var
from .caller import Caller
from .parameter import Parameter
from .profiler import LifecycleProfiler
from core.lifecycle.metrics import LifecycleMetrics
from functools import wraps
from typing import Any


class HLife(LifeCycle):
    """Handler Lifecycle

    Handler 메서드 실행을 추적하고 로깅하기 위한 Lifecycle

    RLife 컨텍스트 내에서 호출되면 Caller에 자동 등록된다.
    """
    handler_name: str
    method_name: str
    params: Parameter
    before_snapshot: Any | None
    after_snapshot: Any | None
    events: list[Any]  # list[Event]
    caller_id: str | None
    _metrics_start_time: float

    @classmethod
    def create(
        cls,
        handler_name: str = "",
        method_name: str = "",
        params: Parameter | None = None,
        **kwargs
    ):
        """HLife 인스턴스 생성"""
        return super().create(
            handler_name=handler_name,
            method_name=method_name,
            params=params or Parameter(args=(), kwargs={}),
            before_snapshot=None,
            after_snapshot=None,
            events=[],
            caller_id=None,
            _metrics_start_time=0.0,
            **kwargs
        )

    def set_snapshot(self, before: Any = None, after: Any = None):
        """Before/After snapshot 설정"""
        if before is not None:
            self.before_snapshot = before
        if after is not None:
            self.after_snapshot = after

    def add_events(self, events: list[Any]):
        """발행할 Event 목록 추가"""
        self.events = events

    @classmethod
    def create_factory(cls, handler_name: str, method_name: str):
        """HLife용 Factory 생성

        handler_name, method_name만 설정한 HLife 인스턴스 생성
        args는 on_enter에서 캡처됨
        """
        def factory():
            return cls.create(
                handler_name=handler_name,
                method_name=method_name
            )
        return factory

    def on_enter(self, func, args, kwargs):
        """진입 시점 hook - args 캡처 및 Caller 등록"""
        # 메트릭 타이머 시작
        self._metrics_start_time = LifecycleMetrics.start_timer()

        # cls 제외한 args, kwargs를 Parameter로 저장
        self.params = Parameter(args=args[1:], kwargs=kwargs)

        # 메트릭 수집
        LifecycleMetrics.hlife_started(
            handler=self.handler_name,
            method=self.method_name
        )

        # 현재 Caller가 있으면 등록
        caller = Caller.get_current()
        if caller:
            caller.register_hlife(self)
            self.caller_id = caller.id

        # Profiler 기록
        profiler = LifecycleProfiler.get_current()
        if profiler:
            profiler.record_begin(
                name=f"{self.handler_name}.{self.method_name}",
                category="HLife",
                args={"caller_id": self.caller_id}
            )

    def on_exit(self):
        """종료 시 로깅 - Hook 오버라이드"""
        # 메트릭 수집
        duration = LifecycleMetrics.get_duration(self._metrics_start_time)
        LifecycleMetrics.hlife_finished(
            handler=self.handler_name,
            method=self.method_name,
            duration=duration
        )

        # Profiler 기록
        profiler = LifecycleProfiler.get_current()
        if profiler:
            event_names = [str(e.event_name) for e in self.events if hasattr(e, 'event_name')]
            profiler.record_end(
                name=f"{self.handler_name}.{self.method_name}",
                category="HLife",
                args={"events": event_names} if event_names else None
            )

        self.close()

    def close(self):
        """Lifecycle 종료 시 로깅"""
        from loguru import logger
        from .sink import emit_lifecycle

        # Events 로깅 처리
        event_names = []
        if self.events:
            for e in self.events:
                if hasattr(e, 'event_name'):
                    event_names.append(str(e.event_name))
                else:
                    event_names.append(str(e))

        emit_lifecycle(self)
        logger.debug(f"{self}")
