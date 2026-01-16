from core.dataobj import DataObj

from dataclasses import dataclass
from .exceptions import InvalidTileException
from functools import cache, lru_cache


class Tile(DataObj):
    __dataclass_config__ = {"frozen": True, "slots": True}
    is_open: bool
    is_mine: bool
    is_flag: bool
    # color: Color | None
    number: int

    @property
    def data(self) -> int:
        d = 0b00000000

        if self.is_open:
            d |= 0b10000000
        if self.is_mine:
            d |= 0b01000000
        if self.is_flag:
            d |= 0b00100000
        if self.number:
            d |= self.number

        # match self.color:
        #     case Color.RED | None:
        #         color_bits = 0
        #     case Color.YELLOW:
        #         color_bits = 1
        #     case Color.BLUE:
        #         color_bits = 2
        #     case Color.PURPLE:
        #         color_bits = 3

        color_bits = 0

        d |= color_bits << 3

        return d

    @cache
    @staticmethod
    def create(
        is_open: bool,
        is_mine: bool,
        is_flag: bool,
        # color: Color | None,
        number: int
    ):
        """
        __init__ 대신 이걸 쓰기를 권장.
        """
        t = Tile(
            is_open=is_open,
            is_mine=is_mine,
            is_flag=is_flag,
            # color=color,
            number=number
        )

        if (t.number is not None) and (t.number > 8 or t.number < 0):
            # 숫자는 음수이거나 8 이상일 수 없음
            # re-> 8이상을 허용해도 될 것 같음
            raise InvalidTileException(t.__dict__)
        if t.is_mine and t.number > 0:
            # 지뢰 타일은 숫자를 가지고있지 않음
            raise InvalidTileException(t.__dict__)
        if is_open and is_flag:
            # 열려있는 타일은 깃발이 꽂혀있을 수 없음
            raise InvalidTileException(t.__dict__)
        # if is_flag and (color is None):
        #     # 색깔 없이 깃발이 꽂혀있을 수 없음
        #     raise InvalidTileException(t.__dict__)
        # if (not is_flag) and (color is not None):
        #     # 깃발이 없는 채로 색깔이 존재할 수 없음
        #     raise InvalidTileException(t.__dict__)

        return t

    @cache
    @staticmethod
    def from_int(b: int):
        is_open = bool(b & 0b10000000)
        is_mine = bool(b & 0b01000000)
        is_flag = bool(b & 0b00100000)

        # color = extract_color(b) if is_flag else None
        number = b & 0b00000111

        t = Tile(
            is_open=is_open,
            is_mine=is_mine,
            is_flag=is_flag,
            # color=color,
            number=number
        )

        if t.is_open and t.is_flag:
            # 열려있는 타일은 깃발이 꽂혀있을 수 없음
            raise InvalidTileException(t.__dict__)

        return t

    def changed(
        self,
        is_open: bool | None = None,
        is_mine: bool | None = None,
        is_flag: bool | None = None,
        number: int | None = None
    ):
        if is_open is None:
            is_open = self.is_open
        if is_mine is None:
            is_mine = self.is_mine
        if is_flag is None:
            is_flag = self.is_flag
        if number is None:
            number = self.number
        return Tile.create(is_open=is_open, is_mine=is_mine, is_flag=is_flag, number=number)


def hide_info(t: Tile):
    return t.changed(is_mine=False, number=0)


# TileEmitter를 클래스 속성으로 할당 (dataclass fields에 포함되지 않도록)
from .tile_emitter import TileEmitter
Tile.emitter = TileEmitter
