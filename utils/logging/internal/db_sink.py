from __future__ import annotations

import json
import sqlite3
import time
from datetime import date, datetime
from enum import Enum
from pathlib import Path
from typing import Any

from core.dataobj import DataObj
from utils.sql import get_sql

SQL_PATH = Path(__file__).with_name("sql")
APP_LOG_INSERT = "app_log_insert.sql"
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


class AppLogDbSink:
    def __init__(self, db_path: str, buffer_size: int = 1):
        self.db_path = db_path
        self.buffer_size = buffer_size
        self._buffer: list[tuple[str, str | None, str | None, int | None, str, str]] = []
        self._db: sqlite3.Connection | None = None

    def __call__(self, message):
        record = message.record
        try:
            self._insert(record)
        except Exception:
            pass

    def stop(self):
        try:
            self._flush()
        except sqlite3.Error:
            pass
        finally:
            if self._db is None:
                return
            self._db.close()
            self._db = None

    def _insert(self, record: dict[str, Any]):
        self._buffer.append(
            (
                record[LOG_RECORD_LEVEL].name,
                record.get(LOG_RECORD_MODULE),
                record.get(LOG_RECORD_FUNCTION),
                record.get(LOG_RECORD_LINE),
                record.get(LOG_RECORD_MESSAGE, ""),
                _to_json(_context(record)),
            )
        )
        if len(self._buffer) >= self.buffer_size:
            self._flush()

    def _flush(self):
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
                if "locked" not in str(e).lower():
                    break
                time.sleep(0.1 * (attempt + 1))

        self._buffer = records + self._buffer
        if last_error is not None:
            raise last_error

    def _get_db(self):
        if self._db is not None:
            return self._db

        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        self._db = sqlite3.connect(
            self.db_path,
            check_same_thread=False,
            timeout=5,
        )
        self._db.execute("PRAGMA busy_timeout = 5000")
        return self._db


def _context(record: dict[str, Any]) -> dict[str, Any]:
    exception = record.get(LOG_RECORD_EXCEPTION)
    context = {
        LOG_RECORD_NAME: record.get(LOG_RECORD_NAME),
        LOG_RECORD_FILE: str(record.get(LOG_RECORD_FILE)),
        LOG_RECORD_PROCESS: str(record.get(LOG_RECORD_PROCESS)),
        LOG_RECORD_THREAD: str(record.get(LOG_RECORD_THREAD)),
        LOG_RECORD_EXTRA: record.get(LOG_RECORD_EXTRA) or {},
    }
    if exception:
        context[LOG_RECORD_EXCEPTION] = str(exception)
    return context


def _to_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, default=_json_default)


def _json_default(value: Any) -> dict[str, Any] | str | list[Any]:
    if isinstance(value, DataObj):
        return value.to_dict()
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, datetime | date):
        return value.isoformat()
    if isinstance(value, set):
        return list(value)
    return str(value)
