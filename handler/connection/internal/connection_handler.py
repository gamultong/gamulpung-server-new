"""
join(WebSocket)
quit(id)

multycast(list[id], external_event)
broadcast(list[id], external_event)
"""

from .conn import Conn

from data.conn import Message
from data.payload import IdPayload

from typing import ClassVar
from core.event import Event
from core.broker import EventBroker


class ConnectionHandler:
    conn_dict: ClassVar[dict[str, Conn]] = {}

    @classmethod
    async def join(cls, conn: Conn):
        ConnectionHandler.conn_dict[conn.id] = conn

        payload = IdPayload(conn.id)
        event = Event(
            event_name="JOIN",
            payload=payload
        )

        await EventBroker.publish(event)

    @classmethod
    async def quit(cls, conn: Conn):
        del ConnectionHandler.conn_dict[conn.id]

        payload = IdPayload(conn.id)
        event = Event(
            event_name="QUIT",
            payload=payload
        )

        await EventBroker.publish(event)

    @classmethod
    async def publish_client_event(cls, event: Event):
        await EventBroker.publish(event)

    @classmethod
    async def multicast(cls, target_ids: list[str], event: Event):
        # TODO: 동기화 문제
        for id in target_ids:
            conn = cls.conn_dict[id]

            msg = Message(event=event)
            await conn.send(msg)

    @classmethod
    async def broadcast(cls, event: Event):
        # TODO: 동기화 문제
        for id, conn in cls.conn_dict.items():
            msg = Message(event=event)
            await conn.send(msg)
