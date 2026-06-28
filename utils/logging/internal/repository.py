from __future__ import annotations

from datetime import date, datetime
from enum import Enum
import json
import os
from typing import TypeAlias

import aiosqlite

from core.dataobj import DataObj
from utils.sql import get_sql

SQL_PATH = os.path.join(os.path.dirname(__file__), "sql") + os.sep

APP_LOG_TABLE_SET = "app_log_table.sql"
APP_LOG_INSERT = "app_log_insert.sql"
APP_LOG_GET_BY_MESSAGE = "app_log_get_by_message.sql"
APP_LOG_RECENT = "app_log_recent.sql"
RECORD_TABLE_NAMES = "record_table_names.sql"
STAT_EVENT_TABLE_SET = "stat_event_table.sql"
STAT_EVENT_INSERT = "stat_event_insert.sql"
STAT_EVENT_CONNECTION_BEFORE = "stat_event_connection_before.sql"
STAT_EVENT_GET_BY_TYPE = "stat_event_get_by_type.sql"
STAT_EVENT_JOIN_LATEST = "stat_event_join_latest.sql"
STAT_EVENT_OBSERVED_RANGE = "stat_event_observed_range.sql"
STAT_EVENT_RECENT = "stat_event_recent.sql"
STAT_EVENT_SINCE = "stat_event_since.sql"
STAT_EVENT_TOTAL_COUNT = "stat_event_total_count.sql"
TABLE_EXISTS = "table_exists.sql"

DB = aiosqlite.Connection
Row = aiosqlite.Row
# JSON 직렬화 가능한 값. 재귀 별칭은 힌팅 이득 대비 복잡해 object로 둔다.
JsonValue: TypeAlias = object
JsonObject: TypeAlias = dict[str, JsonValue]


def to_json(value: JsonValue) -> str:
    return json.dumps(value, ensure_ascii=False, default=_json_default)


def _json_default(value: object) -> JsonValue:
    if isinstance(value, DataObj):
        return value.to_dict()
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, datetime | date):
        return value.isoformat()
    if isinstance(value, set):
        return list(value)
    return str(value)


async def set_app_log_table(db: DB) -> None:
    await db.executescript(get_sql(SQL_PATH, APP_LOG_TABLE_SET))
    await db.commit()


async def set_stat_event_table(db: DB) -> None:
    await db.executescript(get_sql(SQL_PATH, STAT_EVENT_TABLE_SET))
    await db.commit()


async def insert_app_log(
    db: DB,
    *,
    level: str,
    module: str | None,
    function_name: str | None,
    line: int | None,
    message: str,
    context: JsonObject | None = None,
) -> None:
    await db.execute(
        get_sql(SQL_PATH, APP_LOG_INSERT),
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
    payload: JsonObject | None = None,
) -> None:
    await db.execute(
        get_sql(SQL_PATH, STAT_EVENT_INSERT),
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


async def get_record_table_names(db: DB) -> list[str]:
    async with db.execute(get_sql(SQL_PATH, RECORD_TABLE_NAMES)) as cur:
        rows = await cur.fetchall()
    return [row["name"] for row in rows]


async def get_app_log_by_message(db: DB, message: str) -> Row | None:
    if not await table_exists(db, "app_log"):
        return None
    async with db.execute(get_sql(SQL_PATH, APP_LOG_GET_BY_MESSAGE), (message,)) as cur:
        return await cur.fetchone()


async def get_stat_event_by_type(db: DB, event_type: str) -> Row | None:
    if not await table_exists(db, "stat_event"):
        return None
    async with db.execute(get_sql(SQL_PATH, STAT_EVENT_GET_BY_TYPE), (event_type,)) as cur:
        return await cur.fetchone()


async def get_stat_events_since(db: DB, since: str) -> list[Row]:
    if not await table_exists(db, "stat_event"):
        return []
    async with db.execute(get_sql(SQL_PATH, STAT_EVENT_SINCE), (since,)) as cur:
        return await cur.fetchall()


async def get_total_stat_event_count(db: DB) -> int:
    if not await table_exists(db, "stat_event"):
        return 0
    async with db.execute(get_sql(SQL_PATH, STAT_EVENT_TOTAL_COUNT)) as cur:
        row = await cur.fetchone()
    return row["count"] if row is not None else 0


async def get_stat_event_observed_range(db: DB) -> Row | None:
    if not await table_exists(db, "stat_event"):
        return None
    async with db.execute(get_sql(SQL_PATH, STAT_EVENT_OBSERVED_RANGE)) as cur:
        return await cur.fetchone()


async def get_previous_connection_payloads(db: DB, since: str, limit: int) -> list[Row]:
    if not await table_exists(db, "stat_event"):
        return []
    async with db.execute(get_sql(SQL_PATH, STAT_EVENT_CONNECTION_BEFORE), (since, limit)) as cur:
        return await cur.fetchall()


async def get_recent_stat_events(db: DB, limit: int) -> list[Row]:
    if not await table_exists(db, "stat_event"):
        return []
    async with db.execute(get_sql(SQL_PATH, STAT_EVENT_RECENT), (limit,)) as cur:
        return await cur.fetchall()


async def get_recent_app_logs(db: DB, limit: int) -> list[Row]:
    if not await table_exists(db, "app_log"):
        return []
    async with db.execute(get_sql(SQL_PATH, APP_LOG_RECENT), (limit,)) as cur:
        return await cur.fetchall()


async def get_latest_join_times(db: DB) -> list[Row]:
    if not await table_exists(db, "stat_event"):
        return []
    async with db.execute(get_sql(SQL_PATH, STAT_EVENT_JOIN_LATEST)) as cur:
        return await cur.fetchall()


async def table_exists(db: DB, table_name: str) -> bool:
    async with db.execute(get_sql(SQL_PATH, TABLE_EXISTS), (table_name,)) as cur:
        row = await cur.fetchone()
    return row is not None
