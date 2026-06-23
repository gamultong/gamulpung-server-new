from __future__ import annotations

from datetime import date, datetime
from enum import StrEnum
from typing import TypeAlias

from loguru import logger

from core.event import Event, Payload
from core.lifecycle import HLife, LifeCycle, RLife
from data.board import Point, Tile
from data.bomb import InstalledBomb
from data.cursor import Cursor
from data.event import ClientEvent, TriggerEvent
from data.payload import ClientMessage, IdDataPayload, IdPayload
from utils.logging.internal.repository import JsonObject
from utils.stats.internal.event_recorder import enqueue_stat_event

StatPayload: TypeAlias = JsonObject

EVENT_VALUE = 1
NO_DELTA = 0
GRANT_ITEM_AMOUNT_INDEX = 2
GRANT_ITEM_MIN_ARGS = GRANT_ITEM_AMOUNT_INDEX + 1

POSITION_MESSAGE_TYPES = (
    ClientMessage.Move,
    ClientMessage.OpenTiles,
    ClientMessage.SetFlag,
    ClientMessage.DismantleMine,
    ClientMessage.InstallBomb,
)


class HandlerName(StrEnum):
    CURSOR = "CursorHandler"
    BOARD = "BoardHandler"
    BOMB = "BombHandler"


class CursorMethod(StrEnum):
    CREATE = "create"
    DELETE = "delete"
    MOVE = "move"
    DEATH = "death"
    INCREASE_SCORE = "increase_score"
    GRANT_ITEM = "grant_item"


class BoardMethod(StrEnum):
    TOGGLE_FLAG = "toggle_flag"
    OPEN_TILES = "open_tiles"
    DISMANTLE_MINE = "dismantle_mine"


class BombMethod(StrEnum):
    EXPLODE_BOMB = "explode_bomb"


HandlerMethod: TypeAlias = CursorMethod | BoardMethod | BombMethod


class StatEventType(StrEnum):
    JOIN = "JOIN"
    QUIT = "QUIT"
    CREATE_CURSOR = "CREATE_CURSOR"
    MOVE = "MOVE"
    SET_FLAG = "SET_FLAG"
    OPEN_TILE = "OPEN_TILE"
    DISMANTLE_MINE = "DISMANTLE_MINE"
    INSTALL_BOMB = "INSTALL_BOMB"
    EXPLOSION = "EXPLOSION"
    DEATH = "DEATH"
    SCORE_CHANGE = "SCORE_CHANGE"
    GRANT_ITEM = "GRANT_ITEM"


class PayloadKey(StrEnum):
    ACTIVE_AT = "active_at"
    AFTER_ITEMS = "after_items"
    AFTER_SCORE = "after_score"
    BEFORE_ITEMS = "before_items"
    BEFORE_SCORE = "before_score"
    COLOR = "color"
    CONNECTION_COUNT = "connection_count"
    EXPLOSION_RANGE = "explosion_range"
    HAD_CURSOR = "had_cursor"
    HEIGHT = "height"
    IS_MINE = "is_mine"
    ITEM_DELTA = "item_delta"
    REVIVE_AT = "revive_at"
    SCORE_DELTA = "score_delta"
    SOURCE = "source"
    WIDTH = "width"


def record_lifecycle(lifecycle: LifeCycle) -> None:
    try:
        if isinstance(lifecycle, RLife):
            _record_rlife(lifecycle)
        elif isinstance(lifecycle, HLife):
            _record_hlife(lifecycle, actor_id=None)
    except AttributeError as e:
        logger.warning(f"lifecycle 통계 기록 실패 | lifecycle:{type(lifecycle).__name__} error:{e}")


def _record_rlife(rlife: RLife) -> None:
    event_type = _event_name(rlife.event)
    actor_id = _actor_id(rlife.event)
    point = _event_point(rlife.event)
    hlives = _caller_hlives(rlife)

    if event_type == TriggerEvent.JOIN.value:
        _record(StatEventType.JOIN, actor_id=actor_id, value=EVENT_VALUE, payload=_connection_payload())
        return

    if event_type == TriggerEvent.QUIT.value:
        deleted = _first_hlife(hlives, HandlerName.CURSOR, CursorMethod.DELETE)
        deleted_cursor = _cursor_or_none(deleted.before_snapshot if deleted else None)
        _record(
            StatEventType.QUIT,
            actor_id=actor_id,
            point=deleted_cursor.position if deleted_cursor else point,
            value=EVENT_VALUE,
            payload={
                **_connection_payload(),
                PayloadKey.HAD_CURSOR.value: deleted_cursor is not None,
            },
        )
        return

    if event_type == ClientEvent.CREATE_CURSOR.value:
        created = _first_hlife(hlives, HandlerName.CURSOR, CursorMethod.CREATE)
        cursor = _cursor_or_none(created.after_snapshot if created else None)
        _record(
            StatEventType.CREATE_CURSOR,
            actor_id=actor_id,
            point=cursor.position if cursor else point,
            value=EVENT_VALUE,
            payload={
                PayloadKey.WIDTH.value: cursor.width if cursor else None,
                PayloadKey.HEIGHT.value: cursor.height if cursor else None,
                PayloadKey.COLOR.value: int(cursor.color) if cursor else None,
            },
        )
        return

    if event_type == ClientEvent.MOVE.value:
        moved = _first_hlife(hlives, HandlerName.CURSOR, CursorMethod.MOVE)
        if moved is not None:
            _record(StatEventType.MOVE, actor_id=actor_id, point=point, value=EVENT_VALUE)
        return

    if event_type == ClientEvent.SET_FLAG.value:
        toggled = _first_hlife(hlives, HandlerName.BOARD, BoardMethod.TOGGLE_FLAG)
        if toggled is not None:
            _record(
                StatEventType.SET_FLAG,
                actor_id=actor_id,
                point=point,
                value=EVENT_VALUE,
                payload={PayloadKey.SCORE_DELTA.value: _score_delta(hlives)},
            )
        return

    if event_type == ClientEvent.OPEN_TILES.value:
        score_deltas = _score_deltas(hlives)
        for index, hlife in enumerate(_find_hlives(hlives, HandlerName.BOARD, BoardMethod.OPEN_TILES)):
            _record(
                StatEventType.OPEN_TILE,
                actor_id=actor_id,
                point=_first_point_arg(hlife) or point,
                value=EVENT_VALUE,
                payload={
                    PayloadKey.IS_MINE.value: _is_mine(hlife),
                    PayloadKey.SCORE_DELTA.value: score_deltas[index] if index < len(score_deltas) else NO_DELTA,
                },
            )
        return

    if event_type == ClientEvent.DISMANTLE_MINE.value:
        dismantled = _first_hlife(hlives, HandlerName.BOARD, BoardMethod.DISMANTLE_MINE)
        if dismantled is not None:
            _record(
                StatEventType.DISMANTLE_MINE,
                actor_id=actor_id,
                point=point,
                value=EVENT_VALUE,
                payload={PayloadKey.ITEM_DELTA.value: _item_delta(hlives)},
            )
        for hlife in _find_hlives(hlives, HandlerName.BOARD, BoardMethod.OPEN_TILES):
            _record(
                StatEventType.OPEN_TILE,
                actor_id=actor_id,
                point=_first_point_arg(hlife) or point,
                value=EVENT_VALUE,
                payload={
                    PayloadKey.SOURCE.value: StatEventType.DISMANTLE_MINE.value,
                    PayloadKey.IS_MINE.value: _is_mine(hlife),
                },
            )
        return

    if event_type == ClientEvent.INSTALL_BOMB.value and _item_delta(hlives) < NO_DELTA:
        _record(
            StatEventType.INSTALL_BOMB,
            actor_id=actor_id,
            point=point,
            value=EVENT_VALUE,
            payload={PayloadKey.ITEM_DELTA.value: _item_delta(hlives)},
        )


def _record_hlife(hlife: HLife, *, actor_id: str | None) -> None:
    if _is_target_hlife(hlife, HandlerName.BOMB, BombMethod.EXPLODE_BOMB):
        installed_bomb = _installed_bomb_or_none(_first_arg(hlife))
        _record(
            StatEventType.EXPLOSION,
            actor_id=installed_bomb.cur_id if installed_bomb else actor_id,
            point=installed_bomb.position if installed_bomb else None,
            value=installed_bomb.explosion_range if installed_bomb else None,
            payload={
                PayloadKey.EXPLOSION_RANGE.value: installed_bomb.explosion_range if installed_bomb else None,
                PayloadKey.ACTIVE_AT.value: _iso_or_none(installed_bomb.active_at if installed_bomb else None),
            },
        )
        return

    if _is_target_hlife(hlife, HandlerName.CURSOR, CursorMethod.DEATH):
        cursor = _cursor_or_none(hlife.after_snapshot)
        _record(
            StatEventType.DEATH,
            actor_id=cursor.id if cursor else actor_id,
            point=cursor.position if cursor else None,
            value=EVENT_VALUE,
            payload={PayloadKey.REVIVE_AT.value: _iso_or_none(cursor.active_at if cursor else None)},
        )
        return

    if _is_target_hlife(hlife, HandlerName.CURSOR, CursorMethod.INCREASE_SCORE):
        before = _cursor_or_none(hlife.before_snapshot)
        cursor = _cursor_or_none(hlife.after_snapshot)
        _record(
            StatEventType.SCORE_CHANGE,
            actor_id=cursor.id if cursor else actor_id,
            point=cursor.position if cursor else None,
            value=_score_delta_from_hlife(hlife),
            payload={
                PayloadKey.BEFORE_SCORE.value: before.score if before else None,
                PayloadKey.AFTER_SCORE.value: cursor.score if cursor else None,
            },
        )
        return

    if _is_target_hlife(hlife, HandlerName.CURSOR, CursorMethod.GRANT_ITEM):
        before = _cursor_or_none(hlife.before_snapshot)
        cursor = _cursor_or_none(hlife.after_snapshot)
        _record(
            StatEventType.GRANT_ITEM,
            actor_id=cursor.id if cursor else actor_id,
            point=cursor.position if cursor else None,
            value=_item_amount_from_hlife(hlife),
            payload={
                PayloadKey.BEFORE_ITEMS.value: before.items.to_dict() if before else {},
                PayloadKey.AFTER_ITEMS.value: cursor.items.to_dict() if cursor else {},
            },
        )


def _record(
    event_type: StatEventType,
    *,
    actor_id: str | None = None,
    point: Point | None = None,
    value: int | None = None,
    payload: StatPayload | None = None,
) -> None:
    enqueue_stat_event(
        event_type.value,
        actor_id=actor_id,
        point=point,
        value=value,
        payload={key: val for key, val in (payload or {}).items() if val is not None},
    )


def _event_name(event: Event[Payload] | None) -> str | None:
    if event is None:
        return None
    return event.event_name.value


def _actor_id(event: Event[Payload] | None) -> str | None:
    if event is None:
        return None
    payload = event.payload
    if isinstance(payload, (IdPayload, IdDataPayload)):
        return str(payload.id)
    return None


def _event_point(event: Event[Payload] | None) -> Point | None:
    if event is None or not isinstance(event.payload, IdDataPayload):
        return None
    data = event.payload.data
    if isinstance(data, POSITION_MESSAGE_TYPES):
        return data.position
    return None


def _connection_payload() -> StatPayload:
    from handler.connection import ConnectionHandler

    return {PayloadKey.CONNECTION_COUNT.value: len(ConnectionHandler.conn_dict)}


def _caller_hlives(rlife: RLife) -> list[HLife]:
    if rlife.caller is None:
        return []
    return [hlife for hlife in rlife.caller.hlives if isinstance(hlife, HLife)]


def _first_hlife(hlives: list[HLife], handler_name: HandlerName, method_name: HandlerMethod) -> HLife | None:
    return next(iter(_find_hlives(hlives, handler_name, method_name)), None)


def _find_hlives(hlives: list[HLife], handler_name: HandlerName, method_name: HandlerMethod) -> list[HLife]:
    return [
        hlife
        for hlife in hlives
        if _is_target_hlife(hlife, handler_name, method_name)
    ]


def _is_target_hlife(hlife: HLife, handler_name: HandlerName, method_name: HandlerMethod) -> bool:
    return hlife.handler_name == handler_name and hlife.method_name == method_name


def _first_arg(hlife: HLife) -> object | None:
    if hlife.params.args:
        return hlife.params.args[0]
    return None


def _first_point_arg(hlife: HLife) -> Point | None:
    arg = _first_arg(hlife)
    if isinstance(arg, Point):
        return arg
    return None


def _score_delta(hlives: list[HLife]) -> int:
    return sum(
        _score_delta_from_hlife(hlife)
        for hlife in _find_hlives(hlives, HandlerName.CURSOR, CursorMethod.INCREASE_SCORE)
    )


def _score_deltas(hlives: list[HLife]) -> list[int]:
    return [
        _score_delta_from_hlife(hlife)
        for hlife in _find_hlives(hlives, HandlerName.CURSOR, CursorMethod.INCREASE_SCORE)
    ]


def _score_delta_from_hlife(hlife: HLife) -> int:
    before = _cursor_or_none(hlife.before_snapshot)
    after = _cursor_or_none(hlife.after_snapshot)
    if before is None or after is None:
        return NO_DELTA
    return after.score - before.score


def _item_delta(hlives: list[HLife]) -> int:
    return sum(
        _item_amount_from_hlife(hlife)
        for hlife in _find_hlives(hlives, HandlerName.CURSOR, CursorMethod.GRANT_ITEM)
    )


def _item_amount_from_hlife(hlife: HLife) -> int:
    if len(hlife.params.args) < GRANT_ITEM_MIN_ARGS:
        return NO_DELTA
    amount = hlife.params.args[GRANT_ITEM_AMOUNT_INDEX]
    if isinstance(amount, int):
        return amount
    return NO_DELTA


def _is_mine(hlife: HLife) -> bool | None:
    tile = _tile_or_none(hlife.after_snapshot)
    if tile is None:
        return None
    return tile.is_mine


def _cursor_or_none(value: object | None) -> Cursor | None:
    if isinstance(value, Cursor):
        return value
    return None


def _tile_or_none(value: object | None) -> Tile | None:
    if isinstance(value, Tile):
        return value
    return None


def _installed_bomb_or_none(value: object | None) -> InstalledBomb | None:
    if isinstance(value, InstalledBomb):
        return value
    return None


def _iso_or_none(value: object | None) -> str | None:
    if value is None:
        return None
    if isinstance(value, datetime | date):
        return value.isoformat()
    return str(value)
