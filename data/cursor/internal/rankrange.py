from core.dataobj import DataObj
from .cursor import Cursor


class RankRange(DataObj):
    start: int
    end: int


class CursorRankRange(DataObj):
    range: RankRange
    cursors: list[Cursor]

    def iter(self):
        """
        rank, cursor
        """

        for i in range(self.range.start, self.range.end+1):
            idx = i - self.range.start
            yield i, self.cursors[idx]
