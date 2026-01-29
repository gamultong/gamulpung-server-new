"""Tile Emitter 핸들러 함수들

이 모듈이 import되면 데코레이터를 통해 핸들러가 자동 등록됨
"""
from typing import Generator

from core.event import Event
from data.event import InternalEvent
from data.payload import IdPayload, IdDataPayload
from data.board import Point, PointRange, Tile
from .emitter import TileEmitter


@TileEmitter.add()
def notify_tiles_event(old: Tile, new: Tile, point: Point) -> Generator[Event, None, None]:
    """Tile 변경 시 NOTIFY_TILES 이벤트 발행"""
    yield Event(
        event_name=InternalEvent.NOTIFY_TILES,
        payload=IdPayload(id=PointRange(point, point))
    )


@TileEmitter.add()
def explosion_event(old: Tile, new: Tile, point: Point) -> Generator[Event, None, None]:
    """지뢰를 열었을 때 NOTIFY_EXPLOSION 이벤트 발행"""
    if new.is_open and new.is_mine:
        yield Event(
            event_name=InternalEvent.NOTIFY_EXPLOSION,
            payload=IdDataPayload(id=point, data=old)
        )
