from data.board import Tiles, Point, Section, TileKind, CursorTile
from config import BoardConfig


def make_cursor_section(point: Point) -> Section:
    length = BoardConfig.LENGTH
    empty_tile = CursorTile.create(None).data
    tiles = Tiles(
        data=bytearray(empty_tile * (length * length)),
        width=length,
        height=length,
        tile_kind=TileKind.CURSOR
    )
    return Section(point, tiles)
