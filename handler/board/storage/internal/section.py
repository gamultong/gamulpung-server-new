from data.board import Point, Tiles, PointRange, get_overlap, Tile
from dataclasses import dataclass
from enum import IntFlag
from config import BoardConfig


class SectionFlag(IntFlag):
    EMPTY = 0
    CLOSED = 1
    NUMBERING = 2
    INTERACTIONAL = 3


def abs_to_sec(abs_point: Point):
    def to_sec(val):
        return val // BoardConfig.LENGTH

    return Point(
        to_sec(abs_point.x),
        to_sec(abs_point.y)
    )


@dataclass
class Section():
    point: Point
    tiles: Tiles
    flag: SectionFlag = SectionFlag.CLOSED

    @property
    def range(self):
        """section의 범위"""
        l = BoardConfig.LENGTH
        top_left_point = Point(self.point.x * l, (self.point.y + 1) * l - 1)
        bottom_right_point = Point((self.point.x + 1) * l - 1, self.point.y * l)
        return PointRange(
            top_left=top_left_point,
            bottom_right=bottom_right_point
        )

    def at_tiles_by_abs_range(self, point_range: PointRange):
        overlap = get_overlap(self.range, point_range)
        rel_top_left = self.get_point_rel_by_abs(overlap.top_left)
        rel_bottom_right = self.get_point_rel_by_abs(overlap.bottom_right)

        return self.tiles.at_tiles(
            PointRange(rel_top_left, rel_bottom_right)
        )

    def at_tile_by_abs_point(self, point: Point):
        rel_point = self.get_point_rel_by_abs(point)

        return self.tiles.at_tile(rel_point)

    def update_by_abs_point(self, point: Point, tile: Tile):
        rel_point = self.get_point_rel_by_abs(point)

        self.tiles.update_at(rel_point, tile)

    def get_point_rel_by_abs(self, abs_point: Point):
        assert self.range.is_in(abs_point)

        sec_p = abs_to_sec(abs_point)
        length = BoardConfig.LENGTH

        rel_x = abs_point.x - (sec_p.x * length)
        rel_y = abs_point.y - (sec_p.y * length)

        return Point(rel_x, rel_y)
