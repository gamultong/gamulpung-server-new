"""
create(id)
"""
from core.event import Event
from core.broker import EventBroker

from data.cursor import Cursor
from data.payload import IdDataPayload


class CursorHandler:
    cursor_dict: dict[str, Cursor] = {}

    @classmethod
    async def create(cls, cursor: Cursor):
        cls.cursor_dict[cursor.id] = cursor.copy()

        event = Event(
            event_name="NOTIFY-CURSORS",
            payload=IdDataPayload(
                id=cursor.id,
                data=cursor.copy()
            )
        )

        await EventBroker.publish(event=event)

    @classmethod
    async def get_cursors_by_cursor_window(cls, cursor: Cursor) -> list[Cursor]:
        # TODO: 현재는 자기 자신만 보내는 중

        return [cls.cursor_dict[cursor.id].copy()]
