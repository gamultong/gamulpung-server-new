from data.board import PointRange, Point, Section
from handler.board.storage import (
    get_list_by_section_range,
    create_section,
    DB,
)

from .make_section import make_section
from .upgrade_section import _upgrade_interaction_sections, _upgrade_numbering_sections


def set_start_point(section: Section):
    """start point 설정"""
    tile = section.tiles.at_tile(Point(0, 0))

    new_tile = tile.changed(is_mine=False, is_open=True)
    section.tiles.update_at(Point(0, 0), new_tile)


async def check_is_init(db: DB):
    range = PointRange.create_by_mid(Point(0, 0), 2, 2)

    li = await get_list_by_section_range(db, range)
    if len(li) > 0:
        return True

    return False


async def initialize_board(db: DB):
    if await check_is_init(db):
        return

    center_p = Point(0, 0)
    init_board_range = PointRange.create_by_mid(center_p, 2, 2)

    sections = {
        p: make_section(p)
        for p in init_board_range.iter()
    }
    center_sec = sections[center_p]
    set_start_point(center_sec)

    for _, sec in sections.items():
        await create_section(db, sec)

    for p in PointRange.create_by_mid(center_p, 1, 1).iter():
        await _upgrade_numbering_sections(db, p, sections)

    await _upgrade_interaction_sections(db, center_p, sections)
