from data.board import Point, Tile, Tiles, Section, SectionFlag
from handler.board.storage import (
    create_section
)

from .builder import build_tiles

data_str = """\
####
111#
.#1#
111#
"""

tiles = build_tiles(data_str)


async def case_open_tiles_map(db):
    sections = [
        Section(Point(0, 0), tiles.copy(), flag=SectionFlag.INTERACTIONAL)
    ]

    for section in sections:
        await create_section(db, section)
