from __future__ import annotations

from typing import Generator, ClassVar, TYPE_CHECKING, Callable
from core.event import Event
from data.board import Point

if TYPE_CHECKING:
    from .tile import Tile


class TileEmitter:
    """Tile 객체 변경 시 발행할 Event를 관리하는 Emitter

    데코레이터 패턴으로 핸들러를 등록하고, get_events()로 Event 목록 반환
    """
    _update_handlers: ClassVar[list[Callable[[Tile, Tile, Point], Generator[Event, None, None]]]] = []

    @classmethod
    def add(cls) -> Callable:
        """Tile 수정 시 실행할 핸들러 등록 데코레이터

        핸들러 시그니처: (old: Tile, new: Tile, point: Point) -> Generator[Event, None, None]
        """
        def decorator(func: Callable[[Tile, Tile, Point], Generator[Event, None, None]]) -> Callable:
            cls._update_handlers.append(func)
            return func
        return decorator

    @classmethod
    def get_events(cls, old: Tile, new: Tile, point: Point) -> list[Event]:
        """등록된 핸들러를 실행하고 생성된 Event 목록 반환

        Args:
            old: 이전 Tile 상태
            new: 새로운 Tile 상태
            point: Tile의 좌표

        Returns:
            모든 핸들러가 생성한 Event 목록
        """
        events: list[Event] = []

        for handler in cls._update_handlers:
            generator = handler(old, new, point)
            if generator is not None:
                events.extend(list(generator))

        return events

    @classmethod
    def get_dismantle_events(cls, point: Point) -> list[Event]:
        """지뢰 해체 시 발행할 Event 목록 반환

        지뢰 해체는 폭발 이벤트 없이 NOTIFY_TILES만 발행

        Args:
            point: 해체된 지뢰의 좌표

        Returns:
            NOTIFY_TILES 이벤트 목록
        """
        from data.event import InternalEvent
        from data.payload import IdPayload
        from data.board import PointRange

        return [Event(
            event_name=InternalEvent.NOTIFY_TILES,
            payload=IdPayload(id=PointRange(point, point))
        )]


@TileEmitter.add()
def notify_tiles_event(old: Tile, new: Tile, point: Point) -> Generator[Event, None, None]:
    """Tile 변경 시 NOTIFY_TILES 이벤트 발행"""
    from data.event import InternalEvent
    from data.payload import IdPayload
    from data.board import PointRange

    yield Event(
        event_name=InternalEvent.NOTIFY_TILES,
        payload=IdPayload(id=PointRange(point, point))
    )


@TileEmitter.add()
def explosion_event(old: Tile, new: Tile, point: Point) -> Generator[Event, None, None]:
    """지뢰를 열었을 때 NOTIFY_EXPLOSION 이벤트 발행"""
    from data.event import InternalEvent
    from data.payload import IdDataPayload

    if new.is_open and new.is_mine:
        yield Event(
            event_name=InternalEvent.NOTIFY_EXPLOSION,
            payload=IdDataPayload(id=point, data=old)
        )
