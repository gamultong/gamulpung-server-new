from core.lifecycle import HLife, LifeCycle
from data.board import Point, PointRange, CursorTile, abs_to_sec
from handler.board.storage import (
    _get_db,
    create_cursor_section,
    get_cursor_dict_by_section_range,
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
    async def fetch(cls, point_range: PointRange) -> str:
        from handler.cursor import CursorHandler

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

        tile_count = point_range.width * point_range.height
        territory_data = bytearray(tile_count)
        user_color_cache: dict[str, int] = {}

        for idx, point in enumerate(point_range.iter()):
            sec_point = abs_to_sec(point)
            if sec_point not in section_dict:
                section = make_cursor_section(sec_point)
                section_dict[sec_point] = section
            else:
                section = section_dict[sec_point]

            user_id = section.at_cursor_tile_by_abs_point(point).user_id
            if user_id is None:
                territory_data[idx] = 0
                continue

            if user_id in user_color_cache:
                number = user_color_cache[user_id]
            else:
                try:
                    cursor = await CursorHandler.get_by_id(user_id)
                except KeyError:
                    territory_data[idx] = 0
                    continue
                number = int(cursor.color)
                user_color_cache[user_id] = number

            territory_data[idx] = number

        return territory_data.hex()
