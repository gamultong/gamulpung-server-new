from __future__ import annotations

import json
import sqlite3
import time
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import date, datetime
from enum import Enum
from pathlib import Path
from typing import Protocol, TypeAlias, runtime_checkable

from core.dataobj import DataObj
from utils.sql import get_sql

SQL_PATH = Path(__file__).with_name("sql")
APP_LOG_INSERT = "app_log_insert.sql"
DB_BUSY_TIMEOUT_SECONDS = 1
DB_BUSY_TIMEOUT_MS = DB_BUSY_TIMEOUT_SECONDS * 1000
LOG_RECORD_LEVEL = "level"
LOG_RECORD_MODULE = "module"
LOG_RECORD_FUNCTION = "function"
LOG_RECORD_LINE = "line"
LOG_RECORD_MESSAGE = "message"
LOG_RECORD_NAME = "name"
LOG_RECORD_FILE = "file"
LOG_RECORD_PROCESS = "process"
LOG_RECORD_THREAD = "thread"
LOG_RECORD_EXTRA = "extra"
LOG_RECORD_EXCEPTION = "exception"

JsonValue: TypeAlias = None | bool | int | float | str | list["JsonValue"] | dict[str, "JsonValue"]
JsonObject: TypeAlias = dict[str, JsonValue]
LogRecord: TypeAlias = Mapping[str, object]


@runtime_checkable
class LogLevel(Protocol):
    name: str


class LogMessage(Protocol):
    record: LogRecord


@dataclass(frozen=True)
class AppLogContext:
    name: JsonValue
    file: str
    process: str
    thread: str
    extra: JsonValue
    exception: str | None = None

    def to_json(self) -> JsonObject:
        context: JsonObject = {
            LOG_RECORD_NAME: self.name,
            LOG_RECORD_FILE: self.file,
            LOG_RECORD_PROCESS: self.process,
            LOG_RECORD_THREAD: self.thread,
            LOG_RECORD_EXTRA: self.extra,
        }
        if self.exception is not None:
            context[LOG_RECORD_EXCEPTION] = self.exception
        return context


class AppLogDbSink:
    def __init__(self, db_path: str, buffer_size: int = 1):
        self.db_path = db_path
        self.buffer_size = buffer_size
        self._buffer: list[tuple[str, str | None, str | None, int | None, str, str]] = []
        self._db: sqlite3.Connection | None = None

    def __call__(self, message: LogMessage) -> None:
        record = message.record
        try:
            self._insert(record)
        except Exception:
            pass

    def stop(self) -> None:
        try:
            self._flush()
        except sqlite3.Error:
            pass
        finally:
            if self._db is None:
                return
            self._db.close()
            self._db = None

    def _insert(self, record: LogRecord) -> None:
        self._buffer.append(
            (
                _level_name(record.get(LOG_RECORD_LEVEL)),
                _str_or_none(record.get(LOG_RECORD_MODULE)),
                _str_or_none(record.get(LOG_RECORD_FUNCTION)),
                _int_or_none(record.get(LOG_RECORD_LINE)),
                _str_or_empty(record.get(LOG_RECORD_MESSAGE)),
                _to_json(_context(record).to_json()),
            )
        )
        if len(self._buffer) >= self.buffer_size:
            self._flush()

    def _flush(self) -> None:
        if not self._buffer:
            return

        records = self._buffer
        self._buffer = []
        last_error = None
        for attempt in range(3):
            try:
                db = self._get_db()
                db.executemany(
                    get_sql(SQL_PATH, APP_LOG_INSERT),
                    records,
                )
                db.commit()
                return
            except sqlite3.OperationalError as e:
                last_error = e
                # SQLite는 writer가 한 번에 하나라 board/stat/app_log write가 겹치면 lock이 날 수 있다.
                # 로그 저장은 보조 기능이므로 순간 lock에는 잠깐 대기 후 재시도한다.
                if "locked" not in str(e).lower():
                    break
                time.sleep(0.1 * (attempt + 1))

        self._buffer = records + self._buffer
        if last_error is not None:
            raise last_error

    def _get_db(self) -> sqlite3.Connection:
        if self._db is not None:
            return self._db

        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        # 다른 SQLite writer와 겹친 순간 lock에서 바로 실패하지 않도록 connection 대기 시간을 둔다.
        self._db = sqlite3.connect(
            self.db_path,
            check_same_thread=False,
            timeout=DB_BUSY_TIMEOUT_SECONDS,
        )
        # 같은 connection 안의 쿼리에도 동일한 lock 대기 정책을 명시한다.
        self._db.execute(f"PRAGMA busy_timeout = {DB_BUSY_TIMEOUT_MS}")
        return self._db


def _context(record: LogRecord) -> AppLogContext:
    exception = record.get(LOG_RECORD_EXCEPTION)
    return AppLogContext(
        name=_json_value(record.get(LOG_RECORD_NAME)),
        file=str(record.get(LOG_RECORD_FILE)),
        process=str(record.get(LOG_RECORD_PROCESS)),
        thread=str(record.get(LOG_RECORD_THREAD)),
        extra=_json_value(record.get(LOG_RECORD_EXTRA) or {}),
        exception=str(exception) if exception else None,
    )


def _to_json(value: JsonValue) -> str:
    return json.dumps(value, ensure_ascii=False, default=_json_default)


def _json_default(value: object) -> JsonValue:
    return _json_value(value)


def _json_value(value: object | None) -> JsonValue:
    if value is None or isinstance(value, bool | int | float | str):
        return value
    if isinstance(value, DataObj):
        return value.to_dict()
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, datetime | date):
        return value.isoformat()
    if isinstance(value, Mapping):
        return {str(key): _json_value(val) for key, val in value.items()}
    if isinstance(value, Sequence) and not isinstance(value, str | bytes | bytearray):
        return [_json_value(item) for item in value]
    if isinstance(value, set):
        return [_json_value(item) for item in value]
    return str(value)


def _level_name(value: object | None) -> str:
    if isinstance(value, LogLevel):
        return value.name
    return _str_or_empty(value)


def _str_or_none(value: object | None) -> str | None:
    if value is None:
        return None
    return str(value)


def _str_or_empty(value: object | None) -> str:
    if value is None:
        return ""
    return str(value)


def _int_or_none(value: object | None) -> int | None:
    if isinstance(value, int):
        return value
    return None
