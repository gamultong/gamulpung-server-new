import unittest
from unittest.mock import patch

from config import BoardConfig
from data.board import Point, PointRange, Section, SectionFlag
from tests.integration.map.builder import build_tiles

from handler.board.internal.section_handling.numbering import numbering, merge_sections


MAP_S = """\
############
############
############
#####X######
############
########X###
#####X######
############
######X#####
############
############
############
"""

class Test_Numbering_CompareWithBuilderTiles(unittest.TestCase):
    @patch.object(BoardConfig, "LENGTH", 4)
    def test_numbering_matches_builder_numbers(self):
        L = BoardConfig.LENGTH
        center = Point(0, 0)

        # 1) builder가 전체 맵의 number를 미리 채운 big_tiles (정답 타일)
        big_tiles = build_tiles(MAP_S)
        self.assertEqual(big_tiles.width, 3 * L)
        self.assertEqual(big_tiles.height, 3 * L)

        # 2) big_tiles를 9개 섹션으로 split
        sections: dict[Point, Section] = {}
        sec_range = PointRange.create_by_mid(center, 1, 1)

        for sp in sec_range.iter():
            x0 = sp.x * L
            x1 = x0 + L - 1
            y0 = sp.y * L
            y1 = y0 + L - 1

            # abs -> big offset(+L)
            tl = Point(x0 + L, y1 + L)
            br = Point(x1 + L, y0 + L)

            sec_tiles = big_tiles.at_tiles(PointRange(tl, br))
            sections[sp] = Section(sp, sec_tiles)

        # 3) merge가 big_tiles와 같은지 먼저 확인(merge 버그를 바로 잡아냄)
        merged = merge_sections(center, sections)
        self.assertEqual(
            merged, big_tiles,
            msg="merge_sections 결과가 build_tiles의 big_tiles와 다릅니다 (상하/좌우 병합 방향 문제 가능)",
        )

        # 4) numbering 실행
        numbering(center, sections)
        self.assertEqual(sections[center].flag, SectionFlag.NUMBERING)

        # 5) 센터 섹션(LxL)의 각 칸이 big_tiles 중앙(LxL)과 동일한지 비교
        center_sec = sections[center]
        for x in range(L):
            for y in range(L):
                got = center_sec.tiles.at_tile(Point(x, y))
                exp = big_tiles.at_tile(Point(x + L, y + L))  # big_tiles 중앙 영역

                # 지뢰 칸은 둘 다 number=0이어야 함(정상)
                # non-mine은 builder number == numbering number여야 함
                self.assertEqual(
                    got.is_mine, exp.is_mine,
                    msg=f"is_mine mismatch at center local=({x},{y})",
                )
                self.assertEqual(
                    got.number, exp.number,
                    msg=f"number mismatch at center local=({x},{y}) expected={exp.number} got={got.number}",
                )


if __name__ == "__main__":
    unittest.main()
