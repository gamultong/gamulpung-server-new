from __future__ import annotations

from core.dataobj import DataObj
from typing import Generic, TypeVar, ClassVar, Any
from enum import StrEnum, auto


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

        parent = cls.__mro__[1]
        parent_scope = getattr(parent, "__scope__", "")

        # "이 클래스 바디에 직접 적은 조각"만 사용
        scope_part = cls.__dict__.get("__scope_part__", "")

        full_scope = f"{parent_scope}.{scope_part}" if parent_scope and scope_part else (scope_part or parent_scope)
        cls.__scope__ = full_scope


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


class ExternalEvent(EventEnum):
    __scope_part__ = "EXTERNAL"

class ExternalC2SEvent(ExternalEvent):
    __scope_part__ = "C2S"
    CHAT = auto()
    MOVE = auto()
    OPEN_TILES = auto()
    SET_FLAG = auto()
    SET_WINDOW = auto()

class ExternalS2CEvent(ExternalEvent):
    __scope_part__ = "S2C"
    CHAT = auto()
    CURSORS_STATE = auto()
    EXPLOSION = auto()
    SCOREBOARD_STATE = auto()
    TILES_STATE = auto()
    MY_CURSOR = auto()
    QUIT_CURSOR = auto()

class InternalEvent(EventEnum):
    __scope_part__ = "INTERNAL"
    NOTIFY_CURSORS = auto()
    NOTIFY_EXPLOSION = auto()
    NOTIFY_SCOREBOARD = auto()
    NOTIFY_TILES = auto()
    SETTED_WINDOW = auto()

class TriggerEvent(EventEnum):
    __scope_part__ = "TRIGGER"
    JOIN = auto()
    QUIT = auto()


if __name__ == "__main__":
    print(ExternalS2CEvent.CHAT.get_scope())
    print(ExternalS2CEvent.CHAT)
    print(TriggerEvent.JOIN.get_scope())