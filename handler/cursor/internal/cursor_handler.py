"""
create(id)
"""
from core.event import Event
from core.broker import EventBroker

from data.cursor import Cursor, CursorRankRange, RankRange
from data.payload import IdPayload, IdDataPayload
from data.board import is_overlap, PointRange, Point
from data.event import InternalEvent
from datetime import datetime, timedelta

from config import CursorConfig


class CursorHandler:
    cursor_dict: dict[str, Cursor] = {}

    @classmethod
    async def create(cls, cursor: Cursor):
        cls.cursor_dict[cursor.id] = cursor.copy()

        event = Event(
            event_name=InternalEvent.NOTIFY_CURSORS,
            payload=IdPayload(
                id=cursor.id
            )
        )

        await EventBroker.publish(event=event)

    @classmethod
    async def delete(cls, id: str):
        if id in cls.cursor_dict:
            del cls.cursor_dict[id]

    @classmethod
    async def get_by_id(cls, id: str):
        return cls.cursor_dict[id].copy()

    @classmethod
    async def get_cursors_by_cursor_window(cls, cursor: Cursor) -> list[Cursor]:
        snapshot = list(cls.cursor_dict.items())

        return [
            cur.copy()
            for id, cur in snapshot
            if cursor.window.is_in(cur.position)
        ]

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

        rank_range = RankRange(1, 10)
        old_cur_rank_range = await cls.get_cursor_by_rank_range(rank_range)

        await cls.update(new_cur)

        new_cur_rank_range = await cls.get_cursor_by_rank_range(rank_range)
        await cls.scoreboard_modify(old_cur_rank_range, new_cur_rank_range)

        event = Event(
            event_name=InternalEvent.NOTIFY_CURSORS,
            payload=IdDataPayload(
                id=cursor.id,
                data=old_cur
            )
        )
        await EventBroker.publish(event=event)

        event = Event(
            event_name=InternalEvent.SETTED_WINDOW,
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
        new_cur.active_at = datetime.now() + timedelta(seconds=CursorConfig.REVIVE_SECONDS)

        rank_range = RankRange(1, 10)
        old_cur_rank_range = await cls.get_cursor_by_rank_range(rank_range)

        await cls.update(new_cur)

        new_cur_rank_range = await cls.get_cursor_by_rank_range(rank_range)
        await cls.scoreboard_modify(old_cur_rank_range, new_cur_rank_range)

        event = Event(
            event_name=InternalEvent.NOTIFY_CURSORS,
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

        rank_range = RankRange(1, 10)
        old_cur_rank_range = await cls.get_cursor_by_rank_range(rank_range)

        await cls.update(new_cur)

        new_cur_rank_range = await cls.get_cursor_by_rank_range(rank_range)
        await cls.scoreboard_modify(old_cur_rank_range, new_cur_rank_range)

        event = Event(
            event_name=InternalEvent.NOTIFY_CURSORS,
            payload=IdDataPayload(
                id=cursor.id,
                data=old_cur
            )
        )
        await EventBroker.publish(event=event)

    @classmethod
    async def get_cursor_by_rank_range(cls, rank_range: RankRange):
        start = rank_range.start
        end = rank_range.end

        li = sorted(
            (
                cursor
                for key, cursor in cls.cursor_dict.items()
            ),
            reverse=True,
            key=lambda cur: cur.score
        )

        end = end if len(li) > end else len(li)

        return CursorRankRange(
            rank_range,
            li[start-1:end]
        )

    @classmethod
    async def scoreboard_modify(cls, old_cur_range: CursorRankRange, new_cur_range: CursorRankRange):
        old_cursors = old_cur_range.cursors
        new_cursors = new_cur_range.cursors
        if old_cursors != new_cursors:
            event = Event(
                event_name=InternalEvent.NOTIFY_SCOREBOARD,
                payload=IdDataPayload(
                    id=old_cur_range.range,
                    data=old_cur_range
                )
            )

            await EventBroker.publish(event=event)

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
