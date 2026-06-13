"""
create(id)
"""
from core.event import Event
from core.broker import EventBroker
from core.lifecycle import HLife, LifeCycle

from data.cursor import Cursor, CursorRankRange, RankRange, ItemType, Items
from data.cursor.emitter import CursorEmitter
from data.payload import IdPayload, IdDataPayload
from data.board import is_overlap, PointRange, Point, Tiles, TileKind, CursorTile
from data.event import InternalEvent
from datetime import datetime, timedelta

from config import CursorConfig


class CursorHandler:
    cursor_dict: dict[str, Cursor] = {}

    @classmethod
    @LifeCycle.with_async_lifecycle(
        factory=HLife.create_factory("CursorHandler", "create")
    )
    async def create(cls, cursor: Cursor):
        hlife = HLife.get_lifecycle()

        new_cursor = cursor.copy()

        cls.cursor_dict[cursor.id] = new_cursor

        hlife.set_snapshot(before=None, after=new_cursor)

        events = CursorEmitter.get_events(old=None, new=new_cursor)
        hlife.add_events(events)
        for event in events:
            await EventBroker.publish(event=event)

    @classmethod
    @LifeCycle.with_async_lifecycle(
        factory=HLife.create_factory("CursorHandler", "delete")
    )
    async def delete(cls, id: str):
        hlife = HLife.get_lifecycle()
        if id in cls.cursor_dict:
            old_cur = cls.cursor_dict[id].copy()
            del cls.cursor_dict[id]
            hlife.set_snapshot(before=old_cur, after=None)

    @classmethod
    async def get_by_id(cls, id: str):
        return cls.cursor_dict[id].copy()

    @classmethod
    async def to_my_tiles_data(cls, cursor_tiles: Tiles, owner_id: str) -> str:
        assert cursor_tiles.tile_kind == TileKind.CURSOR

        tile_bytes = len(CursorTile.create(None).data)
        tile_count = cursor_tiles.width * cursor_tiles.height
        assert len(cursor_tiles.data) == tile_count * tile_bytes

        my_tiles_data = bytearray(tile_count)

        for idx in range(tile_count):
            start = idx * tile_bytes
            end = start + tile_bytes
            tile = CursorTile.from_bytes(bytes(cursor_tiles.data[start:end]))
            user_id = tile.user_id

            if user_id is None:
                continue

            if user_id == owner_id:
                my_tiles_data[idx] = 1

        return my_tiles_data.hex()

    @classmethod
    async def to_colored_tiles_data(cls, cursor_tiles: Tiles) -> str:
        assert cursor_tiles.tile_kind == TileKind.CURSOR

        tile_bytes = len(CursorTile.create(None).data)
        tile_count = cursor_tiles.width * cursor_tiles.height
        assert len(cursor_tiles.data) == tile_count * tile_bytes

        colored_tiles_data = bytearray(tile_count)
        color_cache: dict[str, int] = {}

        for idx in range(tile_count):
            start = idx * tile_bytes
            end = start + tile_bytes
            tile = CursorTile.from_bytes(bytes(cursor_tiles.data[start:end]))
            user_id = tile.user_id

            if user_id is None:
                continue

            if user_id in color_cache:
                colored_tiles_data[idx] = color_cache[user_id]
                continue

            try:
                cursor = await cls.get_by_id(user_id)
            except KeyError:
                continue

            color_value = int(cursor.color)
            color_cache[user_id] = color_value
            colored_tiles_data[idx] = color_value

        return colored_tiles_data.hex()

    @classmethod
    async def get_cursors_by_cursor_window(cls, cursor: Cursor) -> list[Cursor]:
        snapshot = list(cls.cursor_dict.items())

        return [
            cur.copy()
            for id, cur in snapshot
            if cursor.window.is_in(cur.position)
        ]

    @classmethod
    @LifeCycle.with_async_lifecycle(
        factory=HLife.create_factory("CursorHandler", "move")
    )
    async def move(cls, cursor: Cursor, position: Point):
        hlife = HLife.get_lifecycle()

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

        hlife.set_snapshot(before=old_cur, after=new_cur)

        rank_range = RankRange(1, 10)
        old_cur_rank_range = await cls.get_cursor_by_rank_range(rank_range)

        await cls.update(new_cur)

        new_cur_rank_range = await cls.get_cursor_by_rank_range(rank_range)
        await cls.scoreboard_modify(old_cur_rank_range, new_cur_rank_range)

        events = CursorEmitter.get_events(old=old_cur, new=new_cur)
        hlife.add_events(events)
        for event in events:
            await EventBroker.publish(event=event)

    @classmethod
    @LifeCycle.with_async_lifecycle(
        factory=HLife.create_factory("CursorHandler", "death")
    )
    async def death(cls, cursor: Cursor):
        hlife = HLife.get_lifecycle()

        # old_cur get 없이 cursor 그냥 써도됨
        old_cur = await cls.get_by_id(cursor.id)
        if old_cur.active_at > datetime.now():
            # TODO : exception or skip
            raise "already death"  # type:ignore

        new_cur = old_cur.copy()
        new_cur.score = 0
        new_cur.active_at = datetime.now() + timedelta(seconds=CursorConfig.REVIVE_SECONDS)

        hlife.set_snapshot(before=old_cur, after=new_cur)

        rank_range = RankRange(1, 10)
        old_cur_rank_range = await cls.get_cursor_by_rank_range(rank_range)

        await cls.update(new_cur)

        new_cur_rank_range = await cls.get_cursor_by_rank_range(rank_range)
        await cls.scoreboard_modify(old_cur_rank_range, new_cur_rank_range)

        events = CursorEmitter.get_events(old=old_cur, new=new_cur)
        hlife.add_events(events)
        for event in events:
            await EventBroker.publish(event=event)

    @classmethod
    @LifeCycle.with_async_lifecycle(
        factory=HLife.create_factory("CursorHandler", "increase_score")
    )
    async def increase_score(cls, cursor: Cursor, score: int):
        hlife = HLife.get_lifecycle()

        old_cur = await cls.get_by_id(cursor.id)

        new_cur = old_cur.copy()
        new_cur.score += score

        hlife.set_snapshot(before=old_cur, after=new_cur)

        rank_range = RankRange(1, 10)
        old_cur_rank_range = await cls.get_cursor_by_rank_range(rank_range)

        await cls.update(new_cur)

        new_cur_rank_range = await cls.get_cursor_by_rank_range(rank_range)
        await cls.scoreboard_modify(old_cur_rank_range, new_cur_rank_range)

        events = CursorEmitter.get_events(old=old_cur, new=new_cur)
        hlife.add_events(events)
        for event in events:
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
            RankRange(start, end),
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
    @LifeCycle.with_async_lifecycle(
        factory=HLife.create_factory("CursorHandler", "set_window")
    )
    async def set_window(cls, cursor: Cursor, width: int, height: int):
        hlife = HLife.get_lifecycle()

        old_cur = await cls.get_by_id(cursor.id)

        new_cur = old_cur.copy()
        new_cur.width = width
        new_cur.height = height

        hlife.set_snapshot(before=old_cur, after=new_cur)

        await cls.update(new_cur)

        events = CursorEmitter.get_events(old=old_cur, new=new_cur)
        hlife.add_events(events)
        for event in events:
            await EventBroker.publish(event=event)

    @classmethod
    @LifeCycle.with_async_lifecycle(
        factory=HLife.create_factory("CursorHandler", "grant_item")
    )
    async def grant_item(cls, cursor: Cursor, item_type: ItemType, amount: int):
        hlife = HLife.get_lifecycle()

        old_cur = await cls.get_by_id(cursor.id)

        new_cur = old_cur.copy()
        new_cur.items.grant_item(item_type, amount)

        hlife.set_snapshot(before=old_cur, after=new_cur)

        await cls.update(new_cur)

        events = CursorEmitter.get_events(old=old_cur, new=new_cur)
        hlife.add_events(events)
        for event in events:
            await EventBroker.publish(event=event)

    @classmethod
    async def update(cls, cursor: Cursor):
        cls.cursor_dict[cursor.id] = cursor.copy()

    @classmethod
    async def get_cursor_by_watching_range(cls, range: PointRange):
        from loguru import logger

        result = []
        for key, cursor in cls.cursor_dict.items():
            overlap = is_overlap(range, cursor.window)
            logger.debug(
                f"get_cursor_by_watching_range: cursor_id={cursor.id}, "
                f"cursor.window={cursor.window}, "
                f"range={range}, "
                f"overlap={overlap}"
            )
            if overlap:
                result.append(cursor.copy())

        return result

    @classmethod
    async def get_cursor_in_range(cls, range: PointRange):
        return [
            cursor.copy()
            for key, cursor in cls.cursor_dict.items()
            if range.is_in(cursor.position)
        ]
