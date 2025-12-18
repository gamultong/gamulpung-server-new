from data.board import Point, Tile, Tiles, Section, SectionFlag
from .builder import build_tiles

data1_str = """\
###
#..
#..
"""

data2_str = """\
###
..#
..#
"""

data3_str = """\
#..
#..
###
"""

data4_str = """\
..#
..#
###
"""

tiles1 = build_tiles(data1_str)
tiles2 = build_tiles(data2_str)
tiles3 = build_tiles(data3_str)
tiles4 = build_tiles(data4_str)

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
