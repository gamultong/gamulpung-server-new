from data.board import Point, Tile, Tiles, Section, SectionFlag
from .builder import build_tiles

data1_str = """\
##
#X
"""

data2_str = """\
##
.#
"""

data2_f_str = """\
##
.F
"""

data3_str = """\
##
##
"""

data4_str = """\
##
##
"""

tiles1 = build_tiles(data1_str)
tiles2 = build_tiles(data2_str)
tiles2_f = build_tiles(data2_f_str)
tiles3 = build_tiles(data3_str)
tiles4 = build_tiles(data4_str)

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
