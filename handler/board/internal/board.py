from data.board import PointRange, Tiles, Point, Tile
from data.payload import IdDataPayload
from core.event import Event
from core.broker import EventBroker
from handler.board.storage import _get_db, get_section_range, abs_to_sec, get_section, update_section, SectionFlag

from config import BoardConfig
from .create_section import upgrade_interaction_sections, make_closed_section


class BoardHandler:
    """
    Method
    - fetch(PointRange) -> Tiles

    - open_tiles(Point)
    - togle_flag(Point)
    """

    @classmethod
    async def fetch(cls, point_range: PointRange):
        sec_pr = PointRange(
            abs_to_sec(point_range.top_left),
            abs_to_sec(point_range.bottom_right)
        )

        async with _get_db() as db:
            sections = await get_section_range(db, sec_pr)

        section_dict = {
            section.point: section
            for section in sections
        }

        result = Tiles(bytearray(), point_range.width, 0)
        # top -> bottom 탐색
        for y in range(sec_pr.top, sec_pr.bottom - 1, -1):
            # left -> right 탐색
            line: list[Tiles] = []
            for x in range(sec_pr.left, sec_pr.right + 1):
                sec_point = Point(x, y)

                if sec_point not in section_dict:
                    await make_closed_section(db, sec_point)
                else:
                    section = section_dict[sec_point]

                tiles = section.at_tiles_by_abs_range(point_range)

                line.append(tiles)
            base, *other = line
            # 비용 많이 들어서 한번에 머지
            line_tiles = base.h_append(*other)
            # 비용차 미미
            result = result.v_append(line_tiles)

        assert result.width == point_range.width
        assert result.height == point_range.height

        return result

    @classmethod
    async def togle_flag(cls, point: Point):
        sec_p = abs_to_sec(point)

        async with _get_db() as db:
            section = await get_section(db, sec_p)
            # 섹션이 반드시 존재해야 함
            assert section

            # 섹션이 INTERACTION 상태여야만 상호작용 가능
            if section.flag == SectionFlag.NUMBERING:
                await upgrade_interaction_sections(db, sec_p)

            old_tile = section.at_tile_by_abs_point(point)
            new_tile = old_tile.copy()

            new_tile.is_flag = not new_tile.is_flag

            section.update_by_abs_point(point, new_tile)
            await update_section(db, section)

        event = Event(
            event_name="NOTIFY-TILES",
            payload=IdDataPayload(
                PointRange(point, point),
                data=old_tile
            )
        )

        await EventBroker.publish(event)

    @classmethod
    async def open_tiles(cls, point: Point):
        sec_p = abs_to_sec(point)

        async with _get_db() as db:
            section = await get_section(db, sec_p)
            # 섹션이 반드시 존재해야 함
            assert section

            # 섹션이 INTERACTION 상태여야만 상호작용 가능
            if section.flag == SectionFlag.NUMBERING:
                await upgrade_interaction_sections(db, sec_p)

            old_tile = section.at_tile_by_abs_point(point)
            new_tile = old_tile.copy()

            new_tile.is_open = True

            section.update_by_abs_point(point, new_tile)
            await update_section(db, section)

        event = Event(
            event_name="NOTIFY-TILES",
            payload=IdDataPayload(
                PointRange(point, point),
                data=old_tile
            )
        )

        await EventBroker.publish(event)

    @classmethod
    async def fetch_point(cls, point: Point) -> Tile:
        sec_p = abs_to_sec(point)

        async with _get_db() as db:
            section = await get_section(db, sec_p)
        assert section

        tile = section.at_tile_by_abs_point(point)
        return tile
