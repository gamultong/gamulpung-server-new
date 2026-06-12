from core.lifecycle import HLife, LifeCycle
from data.board import Point, PointRange, CursorTile, Tiles, TileKind, abs_to_sec
from handler.board.storage import (
    get_db,
    create_cursor_section,
    get_cursor_dict_by_section_range,
    get_cursor_list_by_section_range,
    update_cursor_section,
)
from handler.board import make_cursor_section


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

        async with get_db() as db:
            sections = await get_cursor_dict_by_section_range(db, sec_draw_range)
            for sec_p in sec_draw_range.iter():
                if sec_p in sections:
                    continue
                new_section = make_cursor_section(sec_p)
                await create_cursor_section(db, new_section)
                sections[sec_p] = new_section

            for p in draw_point_range.iter():
                sec_p = abs_to_sec(p)
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

        async with get_db() as db:
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
