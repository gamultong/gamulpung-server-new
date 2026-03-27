from core.lifecycle import HLife, LifeCycle
from data.board import Point, PointRange, CursorTile, Tiles, TileKind, Section, abs_to_sec
from handler.board.storage import (
    _get_db,
    create_cursor_section,
    get_cursor_dict_by_section_range,
    get_section,
    get_cursor_list_by_section_range,
    update_cursor_section,
)
from handler.board.internal.section_handling.make_cursor_section import make_cursor_section


class CursorBoardHandler:
    @classmethod
    @LifeCycle.with_async_lifecycle(
        factory=HLife.create_factory("CursorBoardHandler", "draw_board")
    )
    async def draw_board(cls, cur_id: str, point: Point, draw_range: int):
        assert draw_range >= 0

        draw_point_range = PointRange.create_by_mid(point, draw_range, draw_range)
        sec_draw_range = PointRange(
            abs_to_sec(draw_point_range.top_left),
            abs_to_sec(draw_point_range.bottom_right),
        )
        new_tile = CursorTile.create(cur_id)
        changed_sec_points: set[Point] = set()

        async with _get_db() as db:
            sections = await get_cursor_dict_by_section_range(db, sec_draw_range)
            map_sections: dict[Point, Section | None] = {}
            for sec_p in sec_draw_range.iter():
                if sec_p in sections:
                    continue
                new_section = make_cursor_section(sec_p)
                # INSERT OR IGNORE + re-SELECT: DB의 실제 레코드 사용
                existing = await create_cursor_section(db, new_section)
                sections[sec_p] = existing

            for p in draw_point_range.iter():
                sec_p = abs_to_sec(p)
                if sec_p not in map_sections:
                    map_sections[sec_p] = await get_section(db, sec_p)
                map_section = map_sections[sec_p]
                if map_section is None:
                    continue
                map_tile = map_section.at_map_tile_by_abs_point(p)
                if not map_tile.is_open:
                    continue

                section = sections[sec_p]
                old_tile = section.at_cursor_tile_by_abs_point(p)
                if old_tile == new_tile:
                    continue
                section.update_by_abs_point(p, new_tile)
                changed_sec_points.add(sec_p)

            for sec_p in changed_sec_points:
                await update_cursor_section(db, sections[sec_p])

    @classmethod
    @LifeCycle.with_async_lifecycle(
        factory=HLife.create_factory("CursorBoardHandler", "fetch")
    )
    async def fetch(cls, point_range: PointRange) -> Tiles:
        sec_pr = PointRange(
            abs_to_sec(point_range.top_left),
            abs_to_sec(point_range.bottom_right),
        )

        async with _get_db() as db:
            sections = await get_cursor_list_by_section_range(db, sec_pr)

        section_dict = {
            section.point: section
            for section in sections
        }

        result = Tiles(
            data=bytearray(),
            width=point_range.width,
            height=0,
            tile_kind=TileKind.CURSOR,
        )

        for y in range(sec_pr.top, sec_pr.bottom - 1, -1):
            line: list[Tiles] = []
            for x in range(sec_pr.left, sec_pr.right + 1):
                sec_point = Point(x, y)

                if sec_point not in section_dict:
                    section = make_cursor_section(sec_point)
                else:
                    section = section_dict[sec_point]

                tiles = section.at_tiles_by_abs_range(point_range)
                line.append(tiles)

            base, *other = line
            line_tiles = base.h_append(*other)
            result = result.v_append(line_tiles)

        assert result.width == point_range.width
        assert result.height == point_range.height
        assert result.tile_kind == TileKind.CURSOR

        return result
