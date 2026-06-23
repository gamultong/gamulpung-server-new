from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Any

from loguru import logger

from data.board import Point
from handler.board.storage import get_db
from utils.logging import insert_stat_event


@dataclass(frozen=True)
class StatEventRecord:
    event_type: str
    actor_id: str | None
    tile_id: str | None
    x: int | None
    y: int | None
    value: int | None
    payload: dict[str, Any] | None


_stat_event_queue: asyncio.Queue[StatEventRecord | None] | None = None
_stat_event_worker: asyncio.Task[None] | None = None


def tile_id(point: Point | None) -> str | None:
    if point is None:
        return None
    return f"tile:{point.x}:{point.y}"


async def start_stat_event_worker() -> None:
    global _stat_event_queue, _stat_event_worker

    if _stat_event_worker is not None and not _stat_event_worker.done():
        return

    _stat_event_queue = asyncio.Queue()
    _stat_event_worker = asyncio.create_task(_run_stat_event_worker())


async def stop_stat_event_worker() -> None:
    global _stat_event_queue, _stat_event_worker

    queue = _stat_event_queue
    worker = _stat_event_worker
    if queue is None or worker is None:
        return

    await queue.put(None)
    await worker
    _stat_event_queue = None
    _stat_event_worker = None


async def drain_stat_event_queue() -> None:
    if _stat_event_queue is not None:
        await _stat_event_queue.join()


async def record_stat_event(
    event_type: str,
    *,
    actor_id: str | None = None,
    point: Point | None = None,
    value: int | None = None,
    payload: dict[str, Any] | None = None,
) -> None:
    await _insert(_record(event_type, actor_id=actor_id, point=point, value=value, payload=payload))


def enqueue_stat_event(
    event_type: str,
    *,
    actor_id: str | None = None,
    point: Point | None = None,
    value: int | None = None,
    payload: dict[str, Any] | None = None,
) -> None:
    queue = _stat_event_queue
    if queue is None:
        logger.warning(f"stat_event 기록 건너뜀 | reason:worker-not-started event_type:{event_type}")
        return

    queue.put_nowait(_record(event_type, actor_id=actor_id, point=point, value=value, payload=payload))


async def _run_stat_event_worker() -> None:
    queue = _stat_event_queue
    if queue is None:
        return

    while True:
        record = await queue.get()
        try:
            if record is None:
                return
            await _insert(record)
        except Exception as e:
            logger.warning(f"stat_event 기록 실패 | event_type:{getattr(record, 'event_type', None)} error:{e}")
        finally:
            queue.task_done()


def _record(
    event_type: str,
    *,
    actor_id: str | None,
    point: Point | None,
    value: int | None,
    payload: dict[str, Any] | None,
) -> StatEventRecord:
    return StatEventRecord(
        event_type=event_type,
        actor_id=actor_id,
        tile_id=tile_id(point),
        x=point.x if point else None,
        y=point.y if point else None,
        value=value,
        payload=payload,
    )


async def _insert(record: StatEventRecord) -> None:
    async with get_db() as db:
        await insert_stat_event(
            db,
            event_type=record.event_type,
            actor_id=record.actor_id,
            tile_id=record.tile_id,
            x=record.x,
            y=record.y,
            value=record.value,
            payload=record.payload,
        )
