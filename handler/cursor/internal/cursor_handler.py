"""
create(id)
"""
from core.event import Event
from core.broker import EventBroker

from data.cursor import Cursor
from data.payload import IdPayload, IdDataPayload
from data.board import is_overlap, PointRange, Point
from datetime import datetime, timedelta


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
    async def move(cls, cursor: Cursor, position: Point):
        old_cur = await cls.get_by_id(cursor.id)

        old_x = old_cur.position.x
        old_y = old_cur.position.y
        new_x = position.x
        new_y = position.y

        assert old_x-1 <= new_x <= old_x+1
        assert old_y-1 <= new_y <= old_y+1

        new_cur = old_cur.copy()
        new_cur.position = position
        new_cur.score += 1

        await cls.update(new_cur)

        await cls.get_cursor_by_rank_range(1, 10)

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
    async def death(cls, cursor: Cursor):
        # old_cur get 없이 cursor 그냥 써도됨
        old_cur = await cls.get_by_id(cursor.id)
        if old_cur.active_at > datetime.now():
            # TODO : exception or skip
            raise "already death"  # type:ignore

        new_cur = old_cur.copy()
        new_cur.score = 0
        new_cur.active_at = datetime.now() + timedelta(seconds=30)

        await cls.update(new_cur)

        event = Event(
            event_name="NOTIFY-CURSORS",
            payload=IdDataPayload(
                id=cursor.id,
                data=old_cur
            )
        )
        await EventBroker.publish(event=event)

    @classmethod
    async def increase_score(cls, cursor: Cursor, score: int):
        old_cur = await cls.get_by_id(cursor.id)

        new_cur = old_cur.copy()
        new_cur.score += score

        await cls.update(new_cur)

        event = Event(
            event_name="NOTIFY-CURSORS",
            payload=IdDataPayload(
                id=cursor.id,
                data=old_cur
            )
        )
        await EventBroker.publish(event=event)

    @classmethod
    async def get_cursor_by_rank_range(cls, start, end):
        li = sorted(
            (
                cursor
                for key, cursor in cls.cursor_dict.items()
            ),
            reverse=True,
            key=lambda cur: cur.score
        )

        end = end if len(li) > end else len(li)

        return li[start-1:end]

    @classmethod
    async def update(cls, cursor: Cursor):
        cls.cursor_dict[cursor.id] = cursor.copy()

    @classmethod
    async def get_cursor_by_watching_range(cls, range: PointRange):
        return [
            cursor.copy()
            for key, cursor in cls.cursor_dict.items()
            if is_overlap(range, cursor.window)
        ]

    @classmethod
    async def get_cursor_in_range(cls, range: PointRange):
        return [
            cursor.copy()
            for key, cursor in cls.cursor_dict.items()
            if range.is_in(cursor.position)
        ]
