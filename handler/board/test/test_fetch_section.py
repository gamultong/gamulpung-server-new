from tests.utils import TestCase

from data.board import Point, SectionFlag
from handler.board import BoardHandler, initialize_board
from handler.board.storage import get_section


class FetchSection_TestCase(TestCase.UseTable_TestCase):
    async def test_closed_섹션_조회시_격상된_최신_섹션을_반환한다(self):
        """fetch_section이 격상 전 stale 객체를 반환하던 회귀 검증"""
        await initialize_board(self.db)

        # initialize_board 직후 (2, 2)는 CLOSED 상태
        before = await get_section(self.db, Point(2, 2))
        assert before
        self.assertEqual(before.flag, SectionFlag.CLOSED)

        section = await BoardHandler.fetch_section(Point(2, 2))

        self.assertEqual(section.flag, SectionFlag.NUMBERING)
