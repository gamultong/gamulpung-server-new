from data.board import Point, Tile, Tiles
from handler.board import Section, SectionFlag

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

MINE_TILE = Tile(
    is_open=False,
    is_mine=False,
    is_flag=False,
    number=0
).data

FLAGED_TILE = Tile(
    is_open=False,
    is_mine=False,
    is_flag=True,
    number=0
).data

data1 = bytearray([
    CLOSED_TILE, CLOSED_TILE,
    CLOSED_TILE, MINE_TILE,
])
data2 = bytearray([
    CLOSED_TILE, CLOSED_TILE,
    OPENED_TILE, CLOSED_TILE,
])
data2_f = bytearray([
    CLOSED_TILE, CLOSED_TILE,
    OPENED_TILE, FLAGED_TILE,
])
data3 = bytearray([
    CLOSED_TILE, CLOSED_TILE,
    CLOSED_TILE, CLOSED_TILE,
])
data4 = bytearray([
    CLOSED_TILE, CLOSED_TILE,
    CLOSED_TILE, CLOSED_TILE,
])

tiles1 = Tiles(data1, 2, 2)
tiles2 = Tiles(data2, 2, 2)
tiles2_f = Tiles(data2_f, 2, 2)
tiles3 = Tiles(data3, 2, 2)
tiles4 = Tiles(data4, 2, 2)

point1 = Point(-1, 0)
point2 = Point(0, 0)
point3 = Point(-1, -1)
point4 = Point(0, -1)

"""
CC|CC
CX|OC
-----
CC|CC
CC|CC
"""


def case_2_map():
    return {
        point1: Section(point1, tiles1.copy(), flag=SectionFlag.INTERACTIONAL),
        point2: Section(point2, tiles2.copy(), flag=SectionFlag.INTERACTIONAL),
        point3: Section(point3, tiles3.copy(), flag=SectionFlag.INTERACTIONAL),
        point4: Section(point4, tiles4.copy(), flag=SectionFlag.INTERACTIONAL)
    }


def case_2_map_f():
    return {
        point1: Section(point1, tiles1.copy(), flag=SectionFlag.INTERACTIONAL),
        point2: Section(point2, tiles2_f.copy(), flag=SectionFlag.INTERACTIONAL),
        point3: Section(point3, tiles3.copy(), flag=SectionFlag.INTERACTIONAL),
        point4: Section(point4, tiles4.copy(), flag=SectionFlag.INTERACTIONAL)
    }
