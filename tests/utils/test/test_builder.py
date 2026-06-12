from data.board import Point

from tests.utils import build_tiles


class TestBuildTiles:
    def test_비정사각_맵의_width_height가_올바르다(self):
        """Tiles(data, H, W)로 width/height가 뒤집혀 있던 회귀 검증 (정사각 맵에서는 미발현)"""
        # 3행(H=3) x 2열(W=2)
        tiles = build_tiles("""\
X#
##
##
""")

        assert tiles.width == 2
        assert tiles.height == 3

    def test_문자별_타일_의미와_자동_numbering(self):
        tiles = build_tiles("""\
X#
.F
""")

        mine = tiles.map_tile_at(Point(0, 1))
        assert mine.is_mine and not mine.is_open

        closed = tiles.map_tile_at(Point(1, 1))
        assert not closed.is_open
        assert closed.number == 1, "인접 지뢰 수가 자동 계산되어야 함"

        opened = tiles.map_tile_at(Point(0, 0))
        assert opened.is_open

        flagged = tiles.map_tile_at(Point(1, 0))
        assert flagged.is_flag
        assert flagged.number == 1
