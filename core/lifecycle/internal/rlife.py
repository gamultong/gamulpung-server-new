"""Receiver Lifecycle 구현"""
from __future__ import annotations
from contextvars import Token
from .lifecycle import LifeCycle
from .caller import Caller, _caller_var
from .profiler import LifecycleProfiler
from core.event import Event
from loguru import logger


class RLife(LifeCycle):
    """Receiver Lifecycle

    Receiver 함수 실행을 추적하고 로깅하기 위한 Lifecycle

    HLife와 달리:
    - before_snapshot, after_snapshot 없음 (Receiver는 상태 변경 안 함)
    - events 없음 (이미 수신한 event)
    - Event 통째로 저장 (쪼개지 않음)

    Caller를 생성하여 HLife 호출을 추적한다.
    """
    receiver_name: str
    event: Event | None
    caller: Caller | None
    _caller_token: Token | None

    @classmethod
    def create(
        cls,
        receiver_name: str = "",
        event: Event | None = None,
        **kwargs
    ) -> RLife:
        """RLife 인스턴스 생성"""
        return super().create(
            receiver_name=receiver_name,
            event=event,
            caller=None,
            _caller_token=None,
            **kwargs
        )

    @classmethod
    def create_factory(cls):
        """RLife용 Factory

        모든 메타데이터는 on_enter에서 자동 추출
        """
        return cls.create()

    def on_enter(self, func, args, kwargs):
        """진입 시점 hook - 메타데이터 자동 추출 및 Caller 생성"""
        # 함수명 자동 캡처
        self.receiver_name = func.__name__

        # Event 통째로 저장
        if args:
            self.event = args[0]

        # Caller 생성 및 ContextVar 설정
        self.caller = Caller.create(rlife=self)
        self._caller_token = _caller_var.set(self.caller)

        # Profiler 기록
        profiler = LifecycleProfiler.get_current()
        if profiler:
            event_name = str(self.event.event_name) if self.event and hasattr(self.event, 'event_name') else None
            profiler.record_begin(
                name=self.receiver_name,
                category="RLife",
                args={"event": event_name} if event_name else None
            )

    def on_exit(self):
        """종료 시 Caller 정리 및 로깅"""
        # Profiler 기록
        profiler = LifecycleProfiler.get_current()
        if profiler:
            profiler.record_end(
                name=self.receiver_name,
                category="RLife"
            )

        # Caller 정리
        if self.caller:
            self.caller.close()
        if self._caller_token:
            _caller_var.reset(self._caller_token)

        self.close()

    def close(self):
        """Lifecycle 종료 시 로깅"""

        logger.debug(self)
