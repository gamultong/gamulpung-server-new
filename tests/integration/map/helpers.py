"""Helper functions to set up test data in the database"""
from data.board import Section

from handler.board.storage import (
    create_section
)
from .case2 import point1 as case2_point1, point2 as case2_point2, point3 as case2_point3, point4 as case2_point4
from .case2 import tiles1 as case2_tiles1, tiles2 as case2_tiles2, tiles2_f as case2_tiles2_f, tiles3 as case2_tiles3, tiles4 as case2_tiles4
from .case1 import point1 as case1_point1, point2 as case1_point2, point3 as case1_point3, point4 as case1_point4
from .case1 import tiles1 as case1_tiles1, tiles2 as case1_tiles2, tiles3 as case1_tiles3, tiles4 as case1_tiles4


async def setup_case_1_map(db):
    """Set up case_1_map data in the database"""
    sections = [
        Section(case1_point1, case1_tiles1.copy()),
        Section(case1_point2, case1_tiles2.copy()),
        Section(case1_point3, case1_tiles3.copy()),
        Section(case1_point4, case1_tiles4.copy()),
    ]

    for section in sections:
        await create_section(db, section)


async def setup_case_2_map(db):
    """Set up case_2_map data in the database"""
    sections = [
        Section(case2_point1, case2_tiles1.copy()),
        Section(case2_point2, case2_tiles2.copy()),
        Section(case2_point3, case2_tiles3.copy()),
        Section(case2_point4, case2_tiles4.copy()),
    ]

    for section in sections:
        await create_section(db, section)


async def setup_case_2_map_f(db):
    """Set up case_2_map with flag data in the database"""
    sections = [
        Section(case2_point1, case2_tiles1.copy()),
        Section(case2_point2, case2_tiles2_f.copy()),
        Section(case2_point3, case2_tiles3.copy()),
        Section(case2_point4, case2_tiles4.copy()),
    ]

    for section in sections:
        await create_section(db, section)
