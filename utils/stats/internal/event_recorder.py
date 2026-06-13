from __future__ import annotations

import sqlite3
from typing import Any

from loguru import logger

from config import BoardConfig
from data.board import Point
from handler.board.storage import insert_stat_event_sync

DEFAULT_INSERT_TIMEOUT_SECONDS = 0.05
LOCKED_INSERT_TIMEOUT_SECONDS = 1.0
DATABASE_LOCKED_MESSAGE = "database is locked"


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
    _insert_with_lock_retry(record)


def record_stat_event_sync(
    event_type: str,
    *,
    actor_id: str | None = None,
    point: Point | None = None,
    value: int | None = None,
    payload: dict[str, Any] | None = None,
    timeout: float = DEFAULT_INSERT_TIMEOUT_SECONDS,
):
    _insert_with_lock_retry(
        {
            "event_type": event_type,
            "actor_id": actor_id,
            "tile_id": tile_id(point),
            "x": point.x if point else None,
            "y": point.y if point else None,
            "value": value,
            "payload": payload,
        },
        timeout=timeout,
    )


def _insert_with_lock_retry(record: dict[str, Any], *, timeout: float = DEFAULT_INSERT_TIMEOUT_SECONDS):
    timeouts = (timeout, LOCKED_INSERT_TIMEOUT_SECONDS)
    for index, insert_timeout in enumerate(timeouts):
        try:
            _insert(record, timeout=insert_timeout)
            return
        except sqlite3.OperationalError as e:
            if DATABASE_LOCKED_MESSAGE not in str(e):
                raise
            if index == len(timeouts) - 1:
                logger.warning(
                    "stat_event insert skipped because database stayed locked: event_type={} actor_id={}",
                    record.get("event_type"),
                    record.get("actor_id"),
                )
                return


def _insert(record: dict[str, Any], *, timeout: float):
    insert_stat_event_sync(
        BoardConfig.DB_PATH,
        timeout=timeout,
        **record,
    )
