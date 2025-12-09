from data.board import PointRange, Tiles, Point, Section, SectionFlag
from config import BoardConfig


def merge_sections(center: Point, sections: dict[Point, Section]):
    """3*3 크기의 section의 tiles merge 후 return"""
    length = BoardConfig.LENGTH

    result = Tiles(bytearray(), length*3, 0)
    for y in range(center.y-1, center.y+2):
        line = Tiles(bytearray(), 0, length)
        for x in range(center.x-1, center.x+2):
            point = Point(x, y)
            section = sections[point]

            line = line.h_append(section.tiles)
        result = result.v_append(line)

    return result


def count_mine(tiles: Tiles):
    """3*3의 tiles의 가운데 제외 지뢰 갯수"""
    assert tiles.width == tiles.height == 3

    count = 0
    point_range = PointRange(Point(0, 2), Point(2, 0))

    for point in point_range.iter():
        if point == Point(1, 1):
            continue
        tile = tiles.at_tile(point)
        count += tile.is_mine

    return count


def numbering_tiles(tiles: Tiles):
    """merge된 section의 tiles를 받아 가운데 section tiles만 numbering 후 return"""
    length = BoardConfig.LENGTH
    around_range = PointRange(Point(length-1, length*2), Point(length*2, length-1))
    point_range = PointRange(Point(1, length), Point(length, 1))

    around_tiles = tiles.at_tiles(around_range)

    for point in point_range.iter():
        pr = PointRange.create_by_mid(point, 1, 1)
        tiles = around_tiles.at_tiles(pr)
        tile = around_tiles.at_tile(point)
        if tile.is_mine:
            continue
        new_tile = tile.changed(number=count_mine(tiles))

        around_tiles.update_at(point, new_tile)

    result = around_tiles.at_tiles(point_range)
    assert result.width == result.height == length
    return result


def numbering(center: Point, sections: dict[Point, Section]):
    """3*3 section이 주어지면 가운데 section numbering"""
    tiles = merge_sections(center, sections)
    tiles = numbering_tiles(tiles)
    sections[center].tiles = tiles
    sections[center].flag = SectionFlag.NUMBERING
