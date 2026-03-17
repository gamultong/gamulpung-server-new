from __future__ import annotations

import asyncio
import heapq
from loguru import logger

from data.bomb import InstalledBomb
from .bomb import BombHandler


class BombScheduler:
    def __init__(self) -> None:
        self._queue: list[tuple[float, int, str, InstalledBomb]] = []
        self._seq: int = 0
        self._condition = asyncio.Condition()
        self._task: asyncio.Task | None = None
        self._stopped = False

    async def start(self) -> None:
        if self._task and not self._task.done():
            return
        self._stopped = False
        self._task = asyncio.create_task(self._run(), name="bomb_scheduler")
        self._task.add_done_callback(self._log_task_result)

    async def stop(self) -> None:
        if self._task is None:
            return
        async with self._condition:
            self._stopped = True
            self._condition.notify_all()
        try:
            await self._task
        except asyncio.CancelledError:
            pass
        except Exception:
            logger.exception("BombScheduler 종료 중 오류")
        self._task = None

    async def enqueue(self, owner_id: str, bomb: InstalledBomb) -> None:
        async with self._condition:
            self._seq += 1
            heapq.heappush(self._queue, (bomb.active_at_mono, self._seq, owner_id, bomb))
            self._condition.notify()

    async def get_pending_bombs(self) -> list[InstalledBomb]:
        async with self._condition:
            # 활성 시각 기준으로 정렬된 snapshot을 반환한다.
            return [
                bomb.copy()
                for _, _, _, bomb in sorted(self._queue)
            ]

    async def _run(self) -> None:
        loop = asyncio.get_running_loop()
        while True:
            async with self._condition:
                while not self._queue and not self._stopped:
                    await self._condition.wait()
                if self._stopped:
                    return

                while True:
                    active_at_mono, _, owner_id, bomb = self._queue[0]
                    now = loop.time()
                    delay = active_at_mono - now
                    if delay <= 0:
                        heapq.heappop(self._queue)
                        break
                    try:
                        await asyncio.wait_for(self._condition.wait(), timeout=delay)
                    except asyncio.TimeoutError:
                        heapq.heappop(self._queue)
                        break
                    if self._stopped:
                        return

            try:
                await BombHandler.explode_bomb(owner_id, bomb)
            except Exception:
                logger.exception(
                    "폭탄 폭발 처리 실패: owner_id=%s color=%s position=%s",
                    owner_id,
                    int(bomb.color),
                    bomb.position,
                )

    @staticmethod
    def _log_task_result(done_task: asyncio.Task) -> None:
        try:
            done_task.result()
        except asyncio.CancelledError:
            logger.warning("BombScheduler task cancelled")
        except Exception:
            logger.exception("BombScheduler task failed")


_SCHEDULERS: dict[int, BombScheduler] = {}


def _get_scheduler() -> BombScheduler:
    loop = asyncio.get_running_loop()
    key = id(loop)
    scheduler = _SCHEDULERS.get(key)
    if scheduler is None:
        scheduler = BombScheduler()
        _SCHEDULERS[key] = scheduler
    return scheduler


async def start_bomb_scheduler() -> None:
    scheduler = _get_scheduler()
    await scheduler.start()


async def stop_bomb_scheduler() -> None:
    loop = asyncio.get_running_loop()
    key = id(loop)
    scheduler = _SCHEDULERS.get(key)
    if scheduler is None:
        return
    await scheduler.stop()
    _SCHEDULERS.pop(key, None)


async def enqueue_installed_bomb(owner_id: str, bomb: InstalledBomb) -> None:
    scheduler = _get_scheduler()
    await scheduler.start()
    await scheduler.enqueue(owner_id, bomb)


async def get_pending_bombs() -> list[InstalledBomb]:
    scheduler = _get_scheduler()
    await scheduler.start()
    return await scheduler.get_pending_bombs()
