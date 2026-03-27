from __future__ import annotations
from core.dataobj import DataObj
from dataclasses import dataclass
from enum import Enum
from .point import Point, PointRange, get_overlap
from .tile import Tile
from .cursor_tile import CursorTile, CURSOR_TILE_BYTES


"""
123
456
789
-> 123456789
"""


class TileKind(str, Enum):
    MAP = "map"
    CURSOR = "cursor"


class Tiles(DataObj):
    # range 추가
    # data에서 Tile접근 가능하게 해야함
    # property로 width, height 하면 편할 듯?
    data: bytearray
    width: int
    height: int
    tile_kind: TileKind = TileKind.MAP

    def _tile_bytes(self) -> int:
        if self.tile_kind == TileKind.CURSOR:
            return CURSOR_TILE_BYTES
        return 1

    def at_tile(self, point: Point) -> Tile | CursorTile:
        assert 0 <= point.x < self.width
        assert 0 <= point.y < self.height

        idx = (self.height - point.y) - 1
        idx *= self.width
        idx += point.x

        tile_bytes = self._tile_bytes()
        start = idx * tile_bytes
        end = start + tile_bytes
        raw = bytes(self.data[start:end])
        tile = self._tile_from_bytes(raw)

        return tile

    def map_tile_at(self, point: Point) -> Tile:
        assert self.tile_kind == TileKind.MAP
        tile = self.at_tile(point)
        assert isinstance(tile, Tile)
        return tile

    def cursor_tile_at(self, point: Point) -> CursorTile:
        assert self.tile_kind == TileKind.CURSOR
        tile = self.at_tile(point)
        assert isinstance(tile, CursorTile)
        return tile

    def at_tiles(self, point_range: PointRange):
        assert 0 <= point_range.top_left.x <= point_range.bottom_right.x < self.width
        assert 0 <= point_range.bottom_right.y <= point_range.top_left.y < self.height

        data = bytearray()
        width = point_range.width
        height = point_range.height
        tile_bytes = self._tile_bytes()

        for y in range(height):
            y = self.height - (point_range.top_left.y - y) - 1
            row_start = y * self.width
            x_start = row_start + point_range.bottom_left.x
            x_end = row_start + point_range.bottom_right.x + 1
            start = x_start * tile_bytes
            end = x_end * tile_bytes
            law = self.data[start:end]

            data += law

        return Tiles(
            data=data,
            width=width,
            height=height,
            tile_kind=self.tile_kind
        )

    def update_at(self, point: Point, tile: Tile | CursorTile):
        x, y = point.x, self.height - point.y - 1
        idx = x + (y * self.width)
        tile_bytes = self._tile_bytes()
        start = idx * tile_bytes
        end = start + tile_bytes
        self.data[start:end] = self._tile_to_bytes(tile)

    def to_str(self):
        return self.data.hex()

    def hide_info(self) -> 'Tiles':
        """
        타일들의 mine, number 정보를 제거한 새 Tiles를 반환한다.
        타일의 상태가 CLOSED일 때만 해당한다.
        원본 데이터는 변경하지 않는다.
        """
        if self.tile_kind == TileKind.CURSOR:
            return self

        new_data = bytearray(self.data)
        opened = 0b10000000
        mask = 0b10111000
        for idx in range(len(new_data)):
            b = new_data[idx]
            if b & opened:
                continue

            b &= mask
            new_data[idx] = b

        return Tiles(
            data=new_data,
            width=self.width,
            height=self.height,
            tile_kind=self.tile_kind
        )

    def h_append(self, *values: Tiles):
        """가로 병합"""
        for value in values:
            assert self.height == value.height
            assert self.tile_kind == value.tile_kind

        data = bytearray()
        for i in range(self.height):
            line = bytearray()
            for tiles in (self, *values):
                tile_bytes = tiles._tile_bytes()
                start = tiles.width * i * tile_bytes
                end = start + tiles.width * tile_bytes
                line += tiles.data[start:end]

            data += line

        total_width = 0
        for tiles in (self, *values):
            total_width += tiles.width

        return Tiles(
            data=data,
            width=total_width,
            height=self.height,
            tile_kind=self.tile_kind
        )

    def v_append(self, *values: Tiles):
        """세로 병합"""
        for value in values:
            assert self.width == value.width, f"self: {self}\n value:{value}"
            assert self.tile_kind == value.tile_kind

        data = bytearray()
        total_height = 0
        for tiles in (self, *values):
            total_height += tiles.height

            data += tiles.data

        return Tiles(
            data=data,
            width=self.width,
            height=total_height,
            tile_kind=self.tile_kind
        )

    def _tile_from_bytes(self, b: bytes) -> Tile | CursorTile:
        if self.tile_kind == TileKind.CURSOR:
            return CursorTile.from_bytes(b)
        return Tile.from_int(b[0])

    def _tile_to_bytes(self, tile: Tile | CursorTile) -> bytes:
        if self.tile_kind == TileKind.CURSOR:
            assert isinstance(tile, CursorTile)
            return tile.data
        assert isinstance(tile, Tile)
        return bytes([tile.data])

    def to_dict(self):
        hidden = self.hide_info()
        res = super().to_dict()

        res["data"] = hidden.to_str()

        return res

    def __eq__(self, value: Tiles) -> bool:
        r = self.to_str() == value.to_str()
        r &= self.width == value.width
        r &= self.height == value.height
        return r
