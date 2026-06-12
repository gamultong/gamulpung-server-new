"""Cursor Emitter 핸들러 함수들

이 모듈이 import되면 데코레이터를 통해 핸들러가 자동 등록됨
"""
from typing import Generator

from core.event import Event
from data.event import InternalEvent
from data.payload import IdPayload, IdDataPayload
from data.cursor import Cursor
from .emitter import CursorEmitter


@CursorEmitter.add_by_created()
def create_event(new: Cursor) -> Generator[Event, None, None]:
    """Cursor 생성 시 NOTIFY_CURSORS, WINDOW_SET 이벤트 발행"""
    yield Event(
        event_name=InternalEvent.NOTIFY_CURSORS,
        payload=IdPayload(id=new.id)
    )

    yield Event(
        event_name=InternalEvent.WINDOW_SET,
        payload=IdPayload(id=new.id)
    )


@CursorEmitter.add()
def notify_event(old: Cursor, new: Cursor) -> Generator[Event, None, None]:
    """Cursor 수정 시 NOTIFY_CURSORS 이벤트 발행 (변경이 있을 때만)"""
    if old == new:
        return

    yield Event(
        event_name=InternalEvent.NOTIFY_CURSORS,
        payload=IdPayload(id=old.id)
    )


@CursorEmitter.add()
def set_window_event(old: Cursor, new: Cursor) -> Generator[Event, None, None]:
    """위치나 window 크기 변경 시 WINDOW_SET 이벤트 발행"""
    valid = True

    # 위치 변경 없음
    valid &= old.position == new.position
    # window 크기 변경 없음
    valid &= old.width == new.width
    valid &= old.height == new.height

    # 변경 없으면 이벤트 발행 안함
    if valid:
        return

    yield Event(
        event_name=InternalEvent.WINDOW_SET,
        payload=IdDataPayload(id=new.id, data=old)
    )
