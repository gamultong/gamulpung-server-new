from data.board import PointRange, Tiles, Point, Tile, abs_to_sec, SectionFlag
from data.board.emitter import TileEmitter

from core.broker import EventBroker
from core.lifecycle import HLife, LifeCycle
from handler.board.storage import get_db, get_list_by_section_range, get_section, update_section

from .section_handling.upgrade_section import upgrade_interaction_section, upgrade_numbering_section
from .section_handling.make_section import make_closed_section
from loguru import logger


class BoardHandler:
    """
    Method
    - fetch(PointRange) -> Tiles

    - open_tiles(Point)
    - toggle_flag(Point)
    """

    @classmethod
    async def fetch(cls, point_range: PointRange):
        sec_pr = PointRange(
            abs_to_sec(point_range.top_left),
            abs_to_sec(point_range.bottom_right)
        )

        async with get_db() as db:
            sections = await get_list_by_section_range(db, sec_pr)

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
                    section = make_closed_section(sec_point)
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
    @LifeCycle.with_async_lifecycle(
        factory=HLife.create_factory("BoardHandler", "toggle_flag")
    )
    async def toggle_flag(cls, point: Point):
        hlife = HLife.get_lifecycle()

        sec_p = abs_to_sec(point)

        async with get_db() as db:
            section = await get_section(db, sec_p)
            # 섹션이 반드시 존재해야 함
            assert section

            # 섹션이 INTERACTION 상태여야만 상호작용 가능
            if section.flag == SectionFlag.NUMBERING:
                await upgrade_interaction_section(db, sec_p)

            old_tile = section.at_map_tile_by_abs_point(point)
            new_tile = old_tile.changed(is_flag=not old_tile.is_flag)

            hlife.set_snapshot(before=old_tile, after=new_tile)

            section.update_by_abs_point(point, new_tile)
            await update_section(db, section)

        events = TileEmitter.get_events(old=old_tile, new=new_tile, point=point)
        hlife.add_events(events)
        for event in events:
            await EventBroker.publish(event)

    @classmethod
    @LifeCycle.with_async_lifecycle(
        factory=HLife.create_factory("BoardHandler", "open_tiles")
    )
    async def open_tiles(cls, point: Point):
        hlife = HLife.get_lifecycle()

        sec_p = abs_to_sec(point)

        async with get_db() as db:
            section = await get_section(db, sec_p)
            # 섹션이 반드시 존재해야 함
            assert section

            # 섹션이 INTERACTION 상태여야만 상호작용 가능
            if section.flag == SectionFlag.NUMBERING:
                await upgrade_interaction_section(db, sec_p)

            old_tile = section.at_map_tile_by_abs_point(point)

            # 깃발 설치 시 타일 오픈 불가
            if old_tile.is_flag:
                return

            new_tile = old_tile.changed(is_open=True)

            hlife.set_snapshot(before=old_tile, after=new_tile)

            section.update_by_abs_point(point, new_tile)
            await update_section(db, section)

        events = TileEmitter.get_events(old=old_tile, new=new_tile, point=point)
        logger.debug(f"open_tiles 발행 이벤트 | events:{events}")

        hlife.add_events(events)
        for event in events:
            await EventBroker.publish(event)

    @classmethod
    @LifeCycle.with_async_lifecycle(
        factory=HLife.create_factory("BoardHandler", "dismantle_mine")
    )
    async def dismantle_mine(cls, point: Point):
        hlife = HLife.get_lifecycle()

        sec_p = abs_to_sec(point)

        async with get_db() as db:
            section = await get_section(db, sec_p)
            # 섹션이 반드시 존재해야 함
            assert section

            # 섹션이 INTERACTION 상태여야만 상호작용 가능
            if section.flag == SectionFlag.NUMBERING:
                await upgrade_interaction_section(db, sec_p)

            old_tile = section.at_map_tile_by_abs_point(point)

            new_tile = old_tile.changed(is_open=True)

            hlife.set_snapshot(before=old_tile, after=new_tile)

            section.update_by_abs_point(point, new_tile)
            await update_section(db, section)

        events = TileEmitter.get_dismantle_events(point)
        logger.debug(f"dismantle_mine 발행 이벤트 | events:{events}")

        hlife.add_events(events)
        for event in events:
            await EventBroker.publish(event)

    @classmethod
    async def fetch_tile(cls, point: Point) -> Tile:
        sec_p = abs_to_sec(point)

        async with get_db() as db:
            section = await get_section(db, sec_p)
        assert section

        tile = section.at_map_tile_by_abs_point(point)
        return tile

    @classmethod
    async def fetch_section(cls, sec_point: Point):
        async with get_db() as db:
            section = await get_section(db, sec_point)
            assert section

            if section.flag == SectionFlag.CLOSED:
                await upgrade_numbering_section(db, sec_point)
                # 격상 결과(NUMBERING, 지뢰 숫자)를 반영한 최신 섹션을 반환한다
                section = await get_section(db, sec_point)
                assert section

        return section
