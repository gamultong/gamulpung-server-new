from __future__ import annotations

from core.dataobj import DataObj
from typing import Generic, TypeVar
from enum import StrEnum


class Payload(DataObj):
    pass


PAYLOAD_TYPE = TypeVar("PAYLOAD_TYPE", bound=Payload)


class Event(Generic[PAYLOAD_TYPE], DataObj):
    event_name: EventEnum
    payload: PAYLOAD_TYPE


# TODO: client한테 보낼 때 scope 제외
# TODO: chat을 제외한 event들도 테스트와 코드 변경
# 권고사항: EventEnum을 제외한 나머지 Event들 data로 옮기기

class ScopedBase:
    __scope__ = ""          # 누적 결과(자동 생성)
    __scope_part__ = ""     # 이 클래스가 추가하는 조각(직접 선언)

    def __init_subclass__(cls, **kw):
        super().__init_subclass__(**kw)

        # "이 클래스 바디에 직접 적은 조각"만 사용
        scope_part = cls.__dict__.get("__scope_part__", "")

        parent_scope = ""
        for b in cls.__mro__[1:]:
            # b가 직접 __scope__를 가진(스코프 노드인) 클래스만 인정
            if "__scope__" in getattr(b, "__dict__", {}):
                parent_scope = b.__scope__
                break

        parts = [parent_scope, scope_part]
        cls.__scope__ = ".".join(p for p in parts if p)


class EventEnum(ScopedBase, StrEnum):
    @staticmethod
    def _generate_next_value_(name, start, count, last_values) -> str:
        return name

    def __new__(cls, value: str):
        value = value.replace("_", "-")
        obj = str.__new__(cls, value)
        obj._value_ = value
        return obj

    def get_scope(self) -> str:
        return self.__class__.__scope__