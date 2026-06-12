from data.board import Tiles


# 비트 구조는 RFC-006 참고: open(7) mine(6) flag(5) color(4-3) number(2-0)
CLOSED_MINE = 0b01000000
CLOSED_NUMBER_3 = 0b00000011
OPEN_NUMBER_2 = 0b10000010


def make_tiles() -> Tiles:
    return Tiles(
        data=bytearray([CLOSED_MINE, CLOSED_NUMBER_3, OPEN_NUMBER_2, 0]),
        width=4,
        height=1,
    )


class TestHideInfo:
    def test_닫힌_타일의_mine_number가_제거된다(self):
        masked = make_tiles().hide_info()

        assert masked.data[0] == 0, "닫힌 타일의 mine 비트가 제거되어야 함"
        assert masked.data[1] == 0, "닫힌 타일의 number 비트가 제거되어야 함"
        assert masked.data[2] == OPEN_NUMBER_2, "열린 타일은 변형되지 않아야 함"

    def test_원본은_변형되지_않는다(self):
        tiles = make_tiles()
        before = bytes(tiles.data)

        tiles.hide_info()

        assert bytes(tiles.data) == before


class TestTilesToDict:
    def test_값을_반환하고_data는_마스킹된_hex다(self):
        """return 누락 + 원본 파괴 회귀 검증"""
        tiles = make_tiles()
        before = bytes(tiles.data)

        res = tiles.to_dict()

        assert res is not None, "to_dict는 dict를 반환해야 함"
        assert res["data"] == tiles.hide_info().to_str()
        assert bytes(tiles.data) == before, "to_dict가 원본을 변형하면 안 됨"
