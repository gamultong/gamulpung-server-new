from __future__ import annotations

from datetime import date, datetime
from enum import Enum
from functools import cache
import json
import os
from pathlib import Path
import sqlite3
from typing import Any

import aiosqlite

from core.dataobj import DataObj

SQL_PATH = os.path.join(os.path.dirname(__file__), "sql", "log") + os.sep

APP_LOG_TABLE_SET = "app_log_table.sql"
APP_LOG_INSERT = "app_log_insert.sql"
STAT_EVENT_TABLE_SET = "stat_event_table.sql"
STAT_EVENT_INSERT = "stat_event_insert.sql"

DB = aiosqlite.Connection


@cache
def get_sql(path: str):
    with open(f"{SQL_PATH}{path}", "r", encoding="utf-8") as f:
        query = f.read()
    return query


def to_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, default=_json_default)


def _json_default(value: Any):
    if isinstance(value, DataObj):
        return value.to_dict()
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, datetime | date):
        return value.isoformat()
    if isinstance(value, set):
        return list(value)
    return str(value)


async def set_app_log_table(db: DB):
    await db.executescript(get_sql(APP_LOG_TABLE_SET))
    await db.commit()


async def set_stat_event_table(db: DB):
    await db.executescript(get_sql(STAT_EVENT_TABLE_SET))
    await db.commit()


async def insert_app_log(
    db: DB,
    *,
    level: str,
    module: str | None,
    function_name: str | None,
    line: int | None,
    message: str,
    context: dict[str, Any] | None = None,
):
    await db.execute(
        get_sql(APP_LOG_INSERT),
        (
            level,
            module,
            function_name,
            line,
            message,
            to_json(context or {}),
        ),
    )
    await db.commit()


async def insert_stat_event(
    db: DB,
    *,
    event_type: str,
    actor_id: str | None = None,
    tile_id: str | None = None,
    x: int | None = None,
    y: int | None = None,
    value: int | None = None,
    payload: dict[str, Any] | None = None,
):
    await db.execute(
        get_sql(STAT_EVENT_INSERT),
        (
            event_type,
            actor_id,
            tile_id,
            x,
            y,
            value,
            to_json(payload or {}),
        ),
    )
    await db.commit()


def insert_stat_event_sync(
    db_path: str,
    *,
    event_type: str,
    actor_id: str | None = None,
    tile_id: str | None = None,
    x: int | None = None,
    y: int | None = None,
    value: int | None = None,
    payload: dict[str, Any] | None = None,
    timeout: float = 5,
):
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(db_path, timeout=timeout) as db:
        params = (
            event_type,
            actor_id,
            tile_id,
            x,
            y,
            value,
            to_json(payload or {}),
        )
        try:
            db.execute(get_sql(STAT_EVENT_INSERT), params)
        except sqlite3.OperationalError as e:
            if "no such table" not in str(e):
                raise
            db.executescript(get_sql(STAT_EVENT_TABLE_SET))
            db.execute(get_sql(STAT_EVENT_INSERT), params)
