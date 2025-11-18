from unittest.mock import patch
from tests.utils import TestCase
from config import BoardConfig
import tempfile
import os
from handler.board.internal.create_section import initialize_start_map
from handler.board.storage import (
    _get_db,
    set_table,
    get_section,
    get_section_range,
    SectionFlag,
)
from data.board import Point, PointRange

import asyncio


class InitializeStartMap_TestCase(TestCase.UseTable_TestCase):
    def setUp(self) -> None:
        loop = asyncio.get_event_loop()
        loop.set_debug(False)
        super().setUp()

    async def test_section_layer_constraint(self):
        """Section layer 제약이 지켜지는지 확인"""
        await initialize_start_map(self.db)

        point_range = PointRange(Point(-2, 2), Point(2, -2))
        numbering_range = PointRange(Point(-1, 1), Point(1, -1))

        sections = await get_section_range(self.db, point_range)
        sections = {section.point: section for section in sections}

        for x in range(-2, 3):
            for y in range(-2, 3):
                point = Point(x, y)

                section = sections[point]
                if point == Point(0, 0):
                    exp_flag = SectionFlag.INTERACTIONAL
                elif numbering_range.is_in(point):
                    exp_flag = SectionFlag.NUMBERING
                else:
                    exp_flag = SectionFlag.CLOSED

                self.assertEqual(section.flag, exp_flag)

    async def test_start_tile_is_open(self):
        """(0,0) 타일이 열려있는지 확인"""
        await initialize_start_map(self.db)

        center = await get_section(self.db, Point(0, 0))
        assert center

        start_tile = center.at_tile_by_abs_point(Point(0, 0))

        # 지뢰가 없어야 함
        self.assertFalse(start_tile.is_mine)
        # 열려있어야 함
        self.assertTrue(start_tile.is_open)


if __name__ == "__main__":
    from unittest import main
    main()
