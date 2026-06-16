from __future__ import annotations
from core.dataobj import DataObj


class Point(DataObj):
    x: int
    y: int

    def __hash__(self) -> int:
        return (self.x, self.y).__hash__()

    def marshal_bytes(self) -> bytes:
        x_b = self.x.to_bytes(length=8, signed=True)
        y_b = self.y.to_bytes(length=8, signed=True)
        return x_b + y_b

    @staticmethod
    def unmarshal_bytes(b: bytes):
        x = int.from_bytes(bytes=b[:8], signed=True)
        y = int.from_bytes(bytes=b[8:], signed=True)
        return Point(x, y)


class PointRange(DataObj):

    top_left: Point
    bottom_right: Point

    @property
    def extent(self):
        return self.width * self.height

    @property
    def top(self):
        return self.top_left.y

    @property
    def bottom(self):
        return self.bottom_right.y

    @property
    def left(self):
        return self.top_left.x

    @property
    def right(self):
        return self.bottom_right.x

    @property
    def top_right(self):
        return Point(self.bottom_right.x, self.top_left.y)

    @property
    def bottom_left(self):
        return Point(self.top_left.x, self.bottom_right.y)

    @property
    def width(self):
        return self.bottom_right.x - self.top_left.x + 1

    @property
    def height(self):
        return self.top_left.y - self.bottom_right.y + 1

    def is_in(self, point: Point) -> bool:
        return \
            self.top_left.x <= point.x <= self.bottom_right.x and \
            self.top_left.y >= point.y >= self.bottom_right.y

    def iter(self):
        for y in range(self.top, self.bottom-1, -1):
            for x in range(self.left, self.right+1):
                yield Point(x, y)

    @staticmethod
    def create_by_mid(mid: Point, height: int, width: int):
        top_left = Point(mid.x - width, mid.y+height)
        bottom_right = Point(mid.x + width, mid.y-height)
        return PointRange(top_left, bottom_right)


def get_overlap(first: PointRange, second: PointRange):
    if not is_overlap(first, second):
        raise
    top = min(first.top, second.top)
    bottom = max(first.bottom, second.bottom)
    left = max(first.left, second.left)
    right = min(first.right, second.right)

    return PointRange(
        top_left=Point(left, top),
        bottom_right=Point(right, bottom)
    )


def is_overlap(first: PointRange, second: PointRange) -> bool:
    res = False

    res |= first.is_in(second.top_left)
    res |= first.is_in(second.top_right)
    res |= first.is_in(second.bottom_left)
    res |= first.is_in(second.bottom_right)

    res |= second.is_in(first.top_left)
    res |= second.is_in(first.top_right)
    res |= second.is_in(first.bottom_left)
    res |= second.is_in(first.bottom_right)

    return res
