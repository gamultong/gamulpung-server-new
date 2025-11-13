from core.dataobj import DataObj
from .cursor import Cursor


class RankRange(DataObj):
    start: int
    end: int


class CursorRankRange(DataObj):
    range: RankRange
    cursors: list[Cursor]
