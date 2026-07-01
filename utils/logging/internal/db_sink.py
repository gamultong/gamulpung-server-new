from __future__ import annotations

import asyncio
from collections.abc import Callable, Mapping
from contextlib import AbstractAsyncContextManager
from dataclasses import dataclass
from typing import Protocol

from utils.logging.internal.repository import DB, JsonObject, insert_app_log

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

LogRecord = Mapping[str, object]
DBContextFactory = Callable[[], AbstractAsyncContextManager[DB]]


class LogMessage(Protocol):
    record: LogRecord


@dataclass(frozen=True, slots=True)
class AppLogRow:
    level: str
    module: str | None
    function_name: str | None
    line: int | None
    message: str
    context: JsonObject


class AppLogDbSink:
    """loguru sink. record를 큐에 넣고 백그라운드 워커가 aiosqlite(insert_app_log)로 저장한다.

    enqueue=True 로 등록되면 __call__ 이 loguru 워커 스레드에서 불리므로
    loop.call_soon_threadsafe 로 스레드 안전하게 큐에 넣는다.
    start()/stop() 으로 워커 수명을 관리하고, stop() 은 남은 로그를 모두 비운 뒤 반환한다.
    """

    def __init__(self) -> None:
        self._loop: asyncio.AbstractEventLoop | None = None
        self._queue: asyncio.Queue[AppLogRow | None] | None = None
        self._worker: asyncio.Task[None] | None = None
        self._db_factory: DBContextFactory | None = None

    async def start(self, db_factory: DBContextFactory) -> None:
        if self._worker is not None and not self._worker.done():
            return
        self._loop = asyncio.get_running_loop()
        self._db_factory = db_factory
        self._queue = asyncio.Queue()
        self._worker = asyncio.create_task(self._run())

    async def stop(self) -> None:
        loop, queue, worker = self._loop, self._queue, self._worker
        if loop is None or queue is None or worker is None:
            return
        # 이미 예약된 call_soon_threadsafe 큐잉 뒤에 sentinel이 들어가도록 같은 경로로 넣는다.
        loop.call_soon_threadsafe(queue.put_nowait, None)
        await worker
        self._loop = self._queue = self._worker = self._db_factory = None

    def __call__(self, message: LogMessage) -> None:
        loop, queue = self._loop, self._queue
        if loop is None or queue is None:
            return
        loop.call_soon_threadsafe(queue.put_nowait, _row(message.record))

    async def _run(self) -> None:
        queue, db_factory = self._queue, self._db_factory
        if queue is None or db_factory is None:
            return
        async with db_factory() as db:
            while True:
                row = await queue.get()
                try:
                    if row is None:
                        return
                    await insert_app_log(
                        db,
                        level=row.level,
                        module=row.module,
                        function_name=row.function_name,
                        line=row.line,
                        message=row.message,
                        context=row.context,
                    )
                except Exception:
                    # 로그 저장은 보조 기능 — 실패해도 무시한다(여기서 다시 logging하면 재귀 위험).
                    pass
                finally:
                    queue.task_done()


def _row(record: LogRecord) -> AppLogRow:
    line = record.get(LOG_RECORD_LINE)
    return AppLogRow(
        level=_level_name(record.get(LOG_RECORD_LEVEL)),
        module=_str_or_none(record.get(LOG_RECORD_MODULE)),
        function_name=_str_or_none(record.get(LOG_RECORD_FUNCTION)),
        line=line if isinstance(line, int) else None,
        message=str(record.get(LOG_RECORD_MESSAGE) or ""),
        context=_context(record),
    )


def _context(record: LogRecord) -> JsonObject:
    context: JsonObject = {
        LOG_RECORD_NAME: record.get(LOG_RECORD_NAME),
        LOG_RECORD_FILE: str(record.get(LOG_RECORD_FILE)),
        LOG_RECORD_PROCESS: str(record.get(LOG_RECORD_PROCESS)),
        LOG_RECORD_THREAD: str(record.get(LOG_RECORD_THREAD)),
        LOG_RECORD_EXTRA: dict(record.get(LOG_RECORD_EXTRA) or {}),
    }
    exception = record.get(LOG_RECORD_EXCEPTION)
    if exception:
        context[LOG_RECORD_EXCEPTION] = str(exception)
    return context


def _level_name(value: object | None) -> str:
    name = getattr(value, "name", None)
    return name if isinstance(name, str) else str(value or "")


def _str_or_none(value: object | None) -> str | None:
    return None if value is None else str(value)
