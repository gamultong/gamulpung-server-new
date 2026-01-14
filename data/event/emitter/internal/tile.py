from core.event import Event
from data.board import Tile, Point, PointRange
from data.payload import IdPayload, IdDataPayload
from data.event import InternalEvent


def get_tile_events(old: Tile, new: Tile, point: Point) -> list[Event]:
    """Tile 변경에 따른 Event 목록 반환"""
    events: list[Event] = []

    # Tile 변경 시 항상 NOTIFY_TILES 발행
    events.append(Event(
        event_name=InternalEvent.NOTIFY_TILES,
        payload=IdPayload(PointRange(point, point))
    ))

    # 타일이 열렸고 지뢰인 경우 NOTIFY_EXPLOSION 발행
    if new.is_open and new.is_mine:
        events.append(Event(
            event_name=InternalEvent.NOTIFY_EXPLOSION,
            payload=IdDataPayload(point, data=old)
        ))

    return events


def get_mine_dismantle_events(point: Point) -> list[Event]:
    """지뢰 해체에 따른 Events 목록 반환"""
    events: list[Event] = []

    # 지뢰 해체 시 NOTIFY_TILES 발행
    events.append(Event(
        event_name=InternalEvent.NOTIFY_TILES,
        payload=IdPayload(PointRange(point, point))
    ))

    return events
