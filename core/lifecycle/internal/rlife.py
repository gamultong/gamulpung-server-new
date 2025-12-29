"""Receiver Lifecycle 구현"""
from __future__ import annotations
from .lifecycle import LifeCycle
from core.event import Event
from loguru import logger


class RLife(LifeCycle):
    """Receiver Lifecycle

    Receiver 함수 실행을 추적하고 로깅하기 위한 Lifecycle

    HLife와 달리:
    - before_snapshot, after_snapshot 없음 (Receiver는 상태 변경 안 함)
    - events 없음 (이미 수신한 event)
    - Event 통째로 저장 (쪼개지 않음)
    """
    receiver_name: str
    event: Event | None

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
            **kwargs
        )

    @classmethod
    def create_factory(cls):
        """RLife용 Factory

        모든 메타데이터는 on_enter에서 자동 추출
        """
        return cls.create()

    def on_enter(self, func, args, kwargs):
        """진입 시점 hook - 메타데이터 자동 추출"""
        # 함수명 자동 캡처
        self.receiver_name = func.__name__

        # Event 통째로 저장
        if args:
            self.event = args[0]

    def on_exit(self):
        """종료 시 로깅 - Hook 오버라이드"""
        self.close()

    def close(self):
        """Lifecycle 종료 시 로깅"""

        logger.debug(self)
