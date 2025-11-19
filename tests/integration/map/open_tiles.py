from data.board import Point, Tile, Tiles, Section, SectionFlag
from handler.board.storage import (
    create_section
)

TILE = Tile.create(
    is_flag=False,
    is_mine=False,
    is_open=False,
    number=0
)

OPEN = TILE.changed(is_open=True).data
CLSE = TILE.data
NUM1 = TILE.changed(number=1).data

data = [
    CLSE, CLSE, CLSE, CLSE,
    NUM1, NUM1, NUM1, CLSE,
    OPEN, CLSE, NUM1, CLSE,
    NUM1, NUM1, NUM1, CLSE,
]

tiles = Tiles(
    bytearray(data), 4, 4
)


async def case_open_tiles_map(db):
    sections = [
        Section(Point(0, 0), tiles.copy(), flag=SectionFlag.INTERACTIONAL)
    ]

    for section in sections:
        await create_section(db, section)
