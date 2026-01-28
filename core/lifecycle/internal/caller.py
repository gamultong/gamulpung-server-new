"""Caller 구현

RLife와 HLife를 연결하여 Event 인과관계를 추적한다.
"""
from __future__ import annotations
from contextvars import ContextVar
from core.dataobj import DataObj
from core.event import Event
from typing import TYPE_CHECKING, Any
from loguru import logger
import uuid

if TYPE_CHECKING:
    from .rlife import RLife
    from .hlife import HLife

_caller_var: ContextVar[Caller] = ContextVar("caller")


class Caller(DataObj):
    """Caller

    Receiver와 Handler 사이의 연결고리.
    RLife 내에서 호출된 HLife들을 추적한다.
    """
    id: str
    rlife_id: str
    triggering_event: Event | None
    hlives: list[Any]  # list[HLife] - 순환 import 방지

    @classmethod
    def create(cls, rlife: RLife) -> Caller:
        """RLife 정보를 기반으로 Caller 생성"""
        return cls(
            id=str(uuid.uuid4()),
            rlife_id=rlife.id,
            triggering_event=rlife.event,
            hlives=[]
        )

    @classmethod
    def get_current(cls) -> Caller | None:
        """현재 활성 Caller 조회

        RLife 컨텍스트 외부에서 호출 시 None 반환
        """
        return _caller_var.get(None)

    def register_hlife(self, hlife: HLife):
        """HLife 인스턴스 등록"""
        self.hlives.append(hlife)

    def close(self):
        """Caller 종료 시 로깅"""
        logger.debug(f"{self}")
