from data.board import PointRange, Tiles, Point, Tile, get_overlap
from data.payload import ServerMessage
from core.event import Event
from core.broker import EventBroker
from .section import Section, Config

# section 좌표 기준으로 절대 좌표가 어디에 존재하는지 분석


def get_sec_range(sec_point: Point):
    l = Config.LENGTH
    return PointRange(
        top_left=Point(sec_point.x*l, (sec_point.y+1)*l-1),
        bottom_right=Point((sec_point.x+1)*l-1, sec_point.y*l)
    )


def abs_to_rel(abs_point: Point):
    sec_p = abs_to_sec(abs_point)

    def abs_to_rel_int(abs: int, sec: int):
        return abs - (sec * Config.LENGTH)

    return Point(
        abs_to_rel_int(abs_point.x, sec_p.x),
        abs_to_rel_int(abs_point.y, sec_p.y)
    )


def abs_to_sec(abs_point: Point):
    def to_sec(val):
        return val // Config.LENGTH

    return Point(
        to_sec(abs_point.x),
        to_sec(abs_point.y)
    )


def h_append_tiles(left_tiles: Tiles, right_tiles: Tiles):
    assert left_tiles.height == right_tiles.height

    data = bytearray()
    for i in range(left_tiles.height):
        left_index = left_tiles.width * i
        left_index_end = left_index + left_tiles.width
        left_data = left_tiles.data[left_index:left_index_end]

        right_index = right_tiles.width * i
        right_index_end = right_index + right_tiles.width
        right_data = right_tiles.data[right_index:right_index_end]

        data += (left_data + right_data)

    return Tiles(
        data=data,
        width=left_tiles.width+right_tiles.width,
        height=left_tiles.height
    )


def v_merge_tiles(top_tile: Tiles, bottom_tile: Tiles):
    assert top_tile.width == bottom_tile.width

    data = top_tile.data + bottom_tile.data

    return Tiles(
        data=data,
        width=top_tile.width,
        height=top_tile.height+bottom_tile.height
    )


class BoardHandler:
    """
    Method 
    - fetch(PointRange) -> Tiles

    - open_tiles(Point)
    - togle_flag(Point)
    """
    section_dict: dict[Point, Section] = {}

    @classmethod
    async def fetch(cls, point_range: PointRange):
        out_width = point_range.width
        out_height = point_range.height

        section_top_left = abs_to_sec(point_range.top_left)
        section_bottom_right = abs_to_sec(point_range.bottom_right)

        section_top = section_top_left.y
        section_bottom = section_bottom_right.y
        section_left = section_top_left.x
        section_right = section_bottom_right.x

        # 반환할 데이터 공간 미리 할당
        result = Tiles(bytearray(), out_width, 0)

        # top -> bottom 탐색
        for y in range(section_top, section_bottom - 1, -1):
            h_tiles: Tiles | None = None

            # left -> right 탐색
            for x in range(section_left, section_right + 1):
                sec_point = Point(x, y)
                sec_range = get_sec_range(sec_point)

                sec = BoardHandler.section_dict[sec_point]

                overlap = get_overlap(sec_range, point_range)
                rel_range = PointRange(
                    top_left=abs_to_rel(overlap.top_left),
                    bottom_right=abs_to_rel(overlap.bottom_right)
                )

                out_tiles = sec.tiles.at_tiles(rel_range)
                if h_tiles is None:
                    h_tiles = out_tiles
                else:
                    h_tiles = h_merge_tiles(h_tiles, out_tiles)

            assert h_tiles
            result = v_merge_tiles(result, h_tiles)

        assert result.width == out_width
        assert result.height == out_height

        return result

    @classmethod
    async def togle_flag(cls, point: Point):
        sec_p = abs_to_sec(point)
        rel_p = abs_to_rel(point)

        section = BoardHandler.section_dict[sec_p]
        tile = section.tiles.at_tile(rel_p)

        tile.is_flag = not tile.is_flag

        section.tiles.update_at(rel_p, tile)

        # await publish_data_event(BoardEvent.UPDATE, data=tile, id=point)

    @classmethod
    async def open_tiles(cls, point: Point):
        sec_p = abs_to_sec(point)
        rel_p = abs_to_rel(point)

        section = BoardHandler.section_dict[sec_p]
        tile = section.tiles.at_tile(rel_p)

        tile.is_open = True

        section.tiles.update_at(rel_p, tile)

        # await publish_data_event(BoardEvent.UPDATE, data=tile, id=point)

    @classmethod
    async def fetch_point(cls, point: Point) -> Tile:
        tiles = await cls.fetch(PointRange(point, point))
        tile = tiles.at_tile(point)
        return tile
