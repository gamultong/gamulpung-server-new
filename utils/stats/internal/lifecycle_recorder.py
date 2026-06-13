from __future__ import annotations

import sqlite3
from typing import Any

from data.board import Point
from utils.stats.internal.event_recorder import record_stat_event_sync


def record_lifecycle(lifecycle: Any):
    try:
        if lifecycle.__class__.__name__ == "RLife":
            _record_rlife(lifecycle)
        elif lifecycle.__class__.__name__ == "HLife":
            _record_hlife(lifecycle, actor_id=None)
    except (AttributeError, sqlite3.Error):
        pass


def _record_rlife(rlife: Any):
    event_type = _event_name(rlife.event)
    actor_id = _actor_id(rlife.event)
    point = _event_point(rlife.event)
    hlives = list(rlife.caller.hlives) if rlife.caller else []

    if event_type == "JOIN":
        _record("JOIN", actor_id=actor_id, value=1, payload=_connection_payload())
        return

    if event_type == "QUIT":
        deleted = _first_hlife(hlives, "CursorHandler", "delete")
        deleted_cursor = deleted.before_snapshot if deleted else None
        _record(
            "QUIT",
            actor_id=actor_id,
            point=getattr(deleted_cursor, "position", point),
            value=1,
            payload={**_connection_payload(), "had_cursor": deleted_cursor is not None},
        )
        return

    if event_type == "CREATE-CURSOR":
        created = _first_hlife(hlives, "CursorHandler", "create")
        cursor = created.after_snapshot if created else None
        _record(
            "CREATE_CURSOR",
            actor_id=actor_id,
            point=getattr(cursor, "position", point),
            value=1,
            payload={
                "width": getattr(cursor, "width", None),
                "height": getattr(cursor, "height", None),
                "color": _int_or_none(getattr(cursor, "color", None)),
            },
        )
        return

    if event_type == "MOVE":
        moved = _first_hlife(hlives, "CursorHandler", "move")
        if moved is not None:
            _record("MOVE", actor_id=actor_id, point=point, value=1)
        return

    if event_type == "SET-FLAG":
        toggled = _first_hlife(hlives, "BoardHandler", "togle_flag")
        if toggled is not None:
            _record(
                "SET_FLAG",
                actor_id=actor_id,
                point=point,
                value=1,
                payload={"score_delta": _score_delta(hlives)},
            )
        return

    if event_type == "OPEN-TILES":
        score_deltas = _score_deltas(hlives)
        for index, hlife in enumerate(_find_hlives(hlives, "BoardHandler", "open_tiles")):
            _record(
                "OPEN_TILE",
                actor_id=actor_id,
                point=_first_point_arg(hlife) or point,
                value=1,
                payload={
                    "is_mine": _is_mine(hlife),
                    "score_delta": score_deltas[index] if index < len(score_deltas) else 0,
                },
            )
        return

    if event_type == "DISMANTLE-MINE":
        dismantled = _first_hlife(hlives, "BoardHandler", "dismantle_mine")
        if dismantled is not None:
            _record(
                "DISMANTLE_MINE",
                actor_id=actor_id,
                point=point,
                value=1,
                payload={"item_delta": _item_delta(hlives)},
            )
        for hlife in _find_hlives(hlives, "BoardHandler", "open_tiles"):
            _record(
                "OPEN_TILE",
                actor_id=actor_id,
                point=_first_point_arg(hlife) or point,
                value=1,
                payload={"source": "DISMANTLE_MINE", "is_mine": _is_mine(hlife)},
            )
        return

    if event_type == "INSTALL-BOMB":
        if _item_delta(hlives) < 0:
            _record(
                "INSTALL_BOMB",
                actor_id=actor_id,
                point=point,
                value=1,
                payload={"item_delta": _item_delta(hlives)},
            )


def _record_hlife(hlife: Any, *, actor_id: str | None):
    if hlife.handler_name == "BombHandler" and hlife.method_name == "explode_bomb":
        installed_bomb = _first_arg(hlife)
        point = getattr(installed_bomb, "position", None)
        _record(
            "EXPLOSION",
            actor_id=getattr(installed_bomb, "cur_id", actor_id),
            point=point,
            value=getattr(installed_bomb, "explosion_range", None),
            payload={
                "explosion_range": getattr(installed_bomb, "explosion_range", None),
                "active_at": _iso_or_none(getattr(installed_bomb, "active_at", None)),
            },
        )
        return

    if hlife.handler_name == "CursorHandler" and hlife.method_name == "death":
        cursor = hlife.after_snapshot
        _record(
            "DEATH",
            actor_id=getattr(cursor, "id", actor_id),
            point=getattr(cursor, "position", None),
            value=1,
            payload={"revive_at": _iso_or_none(getattr(cursor, "active_at", None))},
        )
        return

    if hlife.handler_name == "CursorHandler" and hlife.method_name == "increase_score":
        cursor = hlife.after_snapshot
        _record(
            "SCORE_CHANGE",
            actor_id=getattr(cursor, "id", actor_id),
            point=getattr(cursor, "position", None),
            value=_score_delta_from_hlife(hlife),
            payload={
                "before_score": getattr(hlife.before_snapshot, "score", None),
                "after_score": getattr(cursor, "score", None),
            },
        )
        return

    if hlife.handler_name == "CursorHandler" and hlife.method_name == "grant_item":
        cursor = hlife.after_snapshot
        before = hlife.before_snapshot
        _record(
            "GRANT_ITEM",
            actor_id=getattr(cursor, "id", actor_id),
            point=getattr(cursor, "position", None),
            value=_item_amount_from_hlife(hlife),
            payload={
                "before_items": before.items.to_dict() if before else {},
                "after_items": cursor.items.to_dict() if cursor else {},
            },
        )
        return


def _record(
    event_type: str,
    *,
    actor_id: str | None = None,
    point: Point | None = None,
    value: int | None = None,
    payload: dict[str, Any] | None = None,
):
    record_stat_event_sync(
        event_type,
        actor_id=actor_id,
        point=point,
        value=value,
        payload={key: val for key, val in (payload or {}).items() if val is not None},
    )


def _event_name(event: Any):
    if event is None:
        return None
    event_name = getattr(event, "event_name", None)
    return getattr(event_name, "value", event_name)


def _actor_id(event: Any):
    return getattr(getattr(event, "payload", None), "id", None)


def _event_point(event: Any):
    data = getattr(getattr(event, "payload", None), "data", None)
    return getattr(data, "position", None)


def _connection_payload():
    from handler.connection import ConnectionHandler

    return {"connection_count": len(ConnectionHandler.conn_dict)}


def _first_hlife(hlives: list[Any], handler_name: str, method_name: str):
    return next(iter(_find_hlives(hlives, handler_name, method_name)), None)


def _find_hlives(hlives: list[Any], handler_name: str, method_name: str):
    return [
        hlife
        for hlife in hlives
        if hlife.handler_name == handler_name and hlife.method_name == method_name
    ]


def _first_arg(hlife: Any):
    if hlife.params.args:
        return hlife.params.args[0]
    return None


def _first_point_arg(hlife: Any):
    arg = _first_arg(hlife)
    if isinstance(arg, Point):
        return arg
    return None


def _score_delta(hlives: list[Any]):
    return sum(
        _score_delta_from_hlife(hlife)
        for hlife in _find_hlives(hlives, "CursorHandler", "increase_score")
    )


def _score_deltas(hlives: list[Any]):
    return [
        _score_delta_from_hlife(hlife)
        for hlife in _find_hlives(hlives, "CursorHandler", "increase_score")
    ]


def _score_delta_from_hlife(hlife: Any):
    before = hlife.before_snapshot
    after = hlife.after_snapshot
    if before is None or after is None:
        return 0
    return after.score - before.score


def _item_delta(hlives: list[Any]):
    return sum(
        _item_amount_from_hlife(hlife)
        for hlife in _find_hlives(hlives, "CursorHandler", "grant_item")
    )


def _item_amount_from_hlife(hlife: Any):
    if len(hlife.params.args) < 3:
        return 0
    amount = hlife.params.args[2]
    if isinstance(amount, int):
        return amount
    return 0


def _is_mine(hlife: Any):
    after = hlife.after_snapshot
    return getattr(after, "is_mine", None)


def _int_or_none(value: Any):
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _iso_or_none(value: Any):
    if value is None:
        return None
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return str(value)
