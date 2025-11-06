"""
create(id)
"""
from core.event import Event
from core.broker import EventBroker

from data.cursor import Cursor
from data.payload import IdPayload, IdDataPayload


class CursorHandler:
    cursor_dict: dict[str, Cursor] = {}

    @classmethod
    async def create(cls, cursor: Cursor):
        cls.cursor_dict[cursor.id] = cursor.copy()

        event = Event(
            event_name="NOTIFY-CURSORS",
            payload=IdPayload(
                id=cursor.id
            )
        )

        await EventBroker.publish(event=event)

        event = Event(
            event_name="SETTED-WINDOW",
            payload=IdPayload(
                id=cursor.id
            )
        )

        await EventBroker.publish(event=event)

    @classmethod
    async def get_by_id(cls, id: str):
        return cls.cursor_dict[id].copy()

    @classmethod
    async def get_cursors_by_cursor_window(cls, cursor: Cursor) -> list[Cursor]:
        # TODO: 현재는 자기 자신만 보내는 중

        return [cls.cursor_dict[cursor.id].copy()]

    @classmethod
    async def move(cls, cursor: Cursor):
        old_cur = await cls.get_by_id(cursor.id)

        old_x = old_cur.position.x
        old_y = old_cur.position.y
        new_x = cursor.position.x
        new_y = cursor.position.y

        assert old_x-1 <= new_x <= old_x+1
        assert old_y-1 <= new_y <= old_y+1

        await cls.update(cursor)

        event = Event(
            event_name="NOTIFY-CURSORS",
            payload=IdDataPayload(
                id=cursor.id,
                data=old_cur
            )
        )
        await EventBroker.publish(event=event)

        event = Event(
            event_name="SETTED-WINDOW",
            payload=IdDataPayload(
                id=cursor.id,
                data=old_cur
            )
        )
        await EventBroker.publish(event=event)

    @classmethod
    async def update(cls, cursor: Cursor):
        cls.cursor_dict[cursor.id] = cursor.copy()
