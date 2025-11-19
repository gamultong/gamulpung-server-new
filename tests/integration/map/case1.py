from data.board import Point, Tile, Tiles, Section, SectionFlag

OPENED_TILE = Tile(
    is_open=True,
    is_mine=False,
    is_flag=False,
    number=0
).data

CLOSED_TILE = Tile(
    is_open=False,
    is_mine=False,
    is_flag=False,
    number=0
).data

data1 = bytearray([
    CLOSED_TILE, CLOSED_TILE, CLOSED_TILE,
    CLOSED_TILE, OPENED_TILE, OPENED_TILE,
    CLOSED_TILE, OPENED_TILE, OPENED_TILE,
])
data2 = bytearray([
    CLOSED_TILE, CLOSED_TILE, CLOSED_TILE,
    OPENED_TILE, OPENED_TILE, CLOSED_TILE,
    OPENED_TILE, OPENED_TILE, CLOSED_TILE,
])
data3 = bytearray([
    CLOSED_TILE, OPENED_TILE, OPENED_TILE,
    CLOSED_TILE, OPENED_TILE, OPENED_TILE,
    CLOSED_TILE, CLOSED_TILE, CLOSED_TILE,
])
data4 = bytearray([
    OPENED_TILE, OPENED_TILE, CLOSED_TILE,
    OPENED_TILE, OPENED_TILE, CLOSED_TILE,
    CLOSED_TILE, CLOSED_TILE, CLOSED_TILE,
])

tiles1 = Tiles(data1, 3, 3)
tiles2 = Tiles(data2, 3, 3)
tiles3 = Tiles(data3, 3, 3)
tiles4 = Tiles(data4, 3, 3)

point1 = Point(-1, 0)
point2 = Point(0, 0)
point3 = Point(-1, -1)
point4 = Point(0, -1)

"""
CCC|CCC
COO|OOC
COO|OOC
-------
COO|OOC
COO|OOC
CCC|CCC
"""


def case_1_map():
    return {
        point1: Section(point1, tiles1.copy(), flag=SectionFlag.INTERACTIONAL),
        point2: Section(point2, tiles2.copy(), flag=SectionFlag.INTERACTIONAL),
        point3: Section(point3, tiles3.copy(), flag=SectionFlag.INTERACTIONAL),
        point4: Section(point4, tiles4.copy(), flag=SectionFlag.INTERACTIONAL)
    }
