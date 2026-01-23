from __future__ import annotations

from typing import Generator, ClassVar, Type, TYPE_CHECKING, Callable
from core.event import Event

if TYPE_CHECKING:
    from .cursor import Cursor


class CursorEmitter:
    """Cursor 객체 변경 시 발행할 Event를 관리하는 Emitter

    데코레이터 패턴으로 핸들러를 등록하고, get_events()로 Event 목록 반환
    """
    _created_handlers: ClassVar[list[Callable[[Cursor], Generator[Event, None, None]]]] = []
    _update_handlers: ClassVar[list[Callable[[Cursor, Cursor], Generator[Event, None, None]]]] = []

    @classmethod
    def add_by_created(cls) -> Callable:
        """Cursor 생성 시 실행할 핸들러 등록 데코레이터

        핸들러 시그니처: (new: Cursor) -> Generator[Event, None, None]
        """
        def decorator(func: Callable[[Cursor], Generator[Event, None, None]]) -> Callable:
            cls._created_handlers.append(func)
            return func
        return decorator

    @classmethod
    def add(cls) -> Callable:
        """Cursor 수정 시 실행할 핸들러 등록 데코레이터

        핸들러 시그니처: (old: Cursor, new: Cursor) -> Generator[Event, None, None]
        """
        def decorator(func: Callable[[Cursor, Cursor], Generator[Event, None, None]]) -> Callable:
            cls._update_handlers.append(func)
            return func
        return decorator

    @classmethod
    def get_events(cls, old: Cursor | None, new: Cursor | None) -> list[Event]:
        """등록된 핸들러를 실행하고 생성된 Event 목록 반환

        Args:
            old: 이전 Cursor 상태 (생성 시 None)
            new: 새로운 Cursor 상태

        Returns:
            모든 핸들러가 생성한 Event 목록
        """
        events: list[Event] = []

        # 생성: old가 None인 경우
        if old is None and new is not None:
            for handler in cls._created_handlers:
                generator = handler(new)
                if generator is not None:
                    events.extend(list(generator))

        # 수정: old와 new 모두 존재
        elif old is not None and new is not None:
            for handler in cls._update_handlers:
                generator = handler(old, new)
                if generator is not None:
                    events.extend(list(generator))

        return events


# 생성시에만
@CursorEmitter.add_by_created()
def create_event(new: Cursor) -> Generator[Event, None, None]:
    from data.event import InternalEvent
    from data.payload import IdPayload

    yield Event(
        event_name=InternalEvent.NOTIFY_CURSORS,
        payload=IdPayload(id=new.id)
    )

    yield Event(
        event_name=InternalEvent.SETTED_WINDOW,
        payload=IdPayload(id=new.id)
    )


@CursorEmitter.add()
def notify_event(old: Cursor, new: Cursor) -> Generator[Event, None, None]:
    from data.event import InternalEvent
    from data.payload import IdPayload

    if old == new:
        return

    yield Event(
        event_name=InternalEvent.NOTIFY_CURSORS,
        payload=IdPayload(id=old.id)
    )


@CursorEmitter.add()
def set_window_event(old: Cursor, new: Cursor) -> Generator[Event, None, None]:
    from data.event import InternalEvent
    from data.payload import IdDataPayload

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
        event_name=InternalEvent.SETTED_WINDOW,
        payload=IdDataPayload(id=new.id, data=old)
    )


# 사용코드 예시
# old:Cursor
# new:Cursor
# new.get_event(old)
