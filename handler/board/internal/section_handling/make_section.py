from data.board import Tiles, Point, Tile, Section

from config import BoardConfig
from random import randint

MINE = Tile(
    is_open=False,
    is_mine=True,
    is_flag=False,
    number=0
).data
TILE = Tile(
    is_open=False,
    is_mine=False,
    is_flag=False,
    number=0
).data


def rand_tile():
    rand = randint(1, 100)
    if 1 <= rand <= BoardConfig.MINE_RATIO * 100:
        return MINE
    else:
        return TILE


def rand_tiles():
    count = 0

    def f():
        nonlocal count
        tile = rand_tile()
        if tile is MINE:
            count += 1
        return tile

    length = BoardConfig.LENGTH
    return Tiles(
        bytearray([
            (f())
            for _ in range(length)
            for _ in range(length)
        ]), length, length
    ), count


def make_closed_section(point: Point):
    length = BoardConfig.LENGTH
    tiles = Tiles(
        bytearray([
            TILE
            for _ in range(length)
            for _ in range(length)
        ]), length, length
    )
    section = Section(point, tiles)

    return section


def make_section(point: Point):
    length = BoardConfig.LENGTH
    m = (length**2) * BoardConfig.MINE_RATIO

    tiles, count = rand_tiles()
    while not (m/2 <= count <= m*2):
        tiles, count = rand_tiles()

    return Section(point, tiles)
