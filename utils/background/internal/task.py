from __future__ import annotations

import asyncio
from typing import Any, Callable, Coroutine

from loguru import logger


def _create_background_task(
    coro: Coroutine[Any, Any, Any],
    *,
    name: str | None = None,
) -> asyncio.Task:
    """코루틴을 백그라운드에서 실행하고 예외를 로깅한다."""
    if name:
        task = asyncio.create_task(coro, name=name)
    else:
        task = asyncio.create_task(coro)

    def _log_result(done_task: asyncio.Task) -> None:
        try:
            done_task.result()
        except asyncio.CancelledError:
            logger.warning(
                "Background task cancelled: %s",
                done_task.get_name(),
            )

    task.add_done_callback(_log_result)
    return task


# 현재는 사용하지 않음
# def run_after_delay(
#     delay_seconds: float,
#     coro_factory: Callable[[], Coroutine[Any, Any, Any]],
#     *,
#     name: str | None = None,
# ) -> asyncio.Task:
#     """지연 후 코루틴을 백그라운드에서 실행한다.
#
#     코루틴을 미리 생성하지 않고, 지연 후 생성해서 await한다.
#     """
#     async def _runner() -> None:
#         await asyncio.sleep(delay_seconds)
#         await coro_factory()
#
#     return _create_background_task(_runner(), name=name)
