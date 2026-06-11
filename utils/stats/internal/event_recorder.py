from __future__ import annotations

import asyncio
import sqlite3
from typing import Any

from config import BoardConfig
from data.board import Point
from handler.board.storage import insert_stat_event_sync


def tile_id(point: Point | None) -> str | None:
    if point is None:
        return None
    return f"tile:{point.x}:{point.y}"


async def record_stat_event(
    event_type: str,
    *,
    actor_id: str | None = None,
    point: Point | None = None,
    value: int | None = None,
    payload: dict[str, Any] | None = None,
):
    record = {
        "event_type": event_type,
        "actor_id": actor_id,
        "tile_id": tile_id(point),
        "x": point.x if point else None,
        "y": point.y if point else None,
        "value": value,
        "payload": payload,
    }
    try:
        _insert(record, timeout=0.05)
    except sqlite3.OperationalError as e:
        if "database is locked" not in str(e):
            raise
        asyncio.create_task(_retry(record))


def _insert(record: dict[str, Any], *, timeout: float):
    insert_stat_event_sync(
        BoardConfig.DB_PATH,
        timeout=timeout,
        **record,
    )


async def _retry(record: dict[str, Any]):
    for delay in (0.1, 0.2, 0.5, 1, 2):
        await asyncio.sleep(delay)
        try:
            _insert(record, timeout=0.1)
            return
        except sqlite3.OperationalError as e:
            if "database is locked" not in str(e):
                return
