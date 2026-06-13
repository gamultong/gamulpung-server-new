from __future__ import annotations
import asyncio
from typing import Callable, Coroutine
from core.event import Event
from loguru import logger

EVENT_COUNT = 0


class Receiver:
    def __init__(self, func: Callable[[Event], Coroutine], event_name: str):
        self.func = func
        self.event_name = event_name

    async def __call__(self, event: Event):
        return await self.func(event)

    def __str__(self):
        return f"<Receiver {self.event_name} -> {self.func}({self.func.__name__})>"


class EventBroker:
    event_dict: dict[str, list[Receiver]] = {}
    _idle_event: asyncio.Event | None = None
    _idle_loop: asyncio.AbstractEventLoop | None = None

    @staticmethod
    def add_receiver(event_name: str):
        if event_name not in EventBroker.event_dict:
            EventBroker.event_dict[event_name] = []

        def wrapper(func: Callable[[Event], Coroutine] | Receiver):
            logger.debug(f"add_receiver {event_name}")
            if isinstance(func, Receiver):
                func = func.func

            receiver = Receiver(func, event_name)

            EventBroker.event_dict[event_name].append(receiver)
            return receiver

        return wrapper

    @staticmethod
    async def publish(event: Event):
        logger.debug(f"event-publish: \n{event}")
        coroutines = []

        receivers = EventBroker.event_dict[event.event_name]

        async def counter(receiver, event):
            global EVENT_COUNT
            EVENT_COUNT += 1
            EventBroker._mark_running()
            try:
                await receiver(event)
            finally:
                EVENT_COUNT -= 1
                EventBroker._mark_done()

        for receiver in receivers:
            coroutines.append(counter(receiver, event))

        await asyncio.gather(*coroutines)

    @staticmethod
    def is_end():
        if EVENT_COUNT == 0:
            return True
        else:
            return False

    @staticmethod
    async def wait_until_idle(timeout: float | None = None):
        event = EventBroker._get_idle_event()
        await asyncio.wait_for(event.wait(), timeout=timeout)

    @staticmethod
    def _get_idle_event():
        loop = asyncio.get_running_loop()
        if EventBroker._idle_event is None or EventBroker._idle_loop is not loop:
            EventBroker._idle_event = asyncio.Event()
            EventBroker._idle_loop = loop
            if EventBroker.is_end():
                EventBroker._idle_event.set()
        return EventBroker._idle_event

    @staticmethod
    def _mark_running():
        event = EventBroker._get_idle_event()
        event.clear()

    @staticmethod
    def _mark_done():
        if EventBroker.is_end():
            event = EventBroker._get_idle_event()
            event.set()
