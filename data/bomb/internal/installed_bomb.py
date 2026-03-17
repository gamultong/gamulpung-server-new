from core.dataobj import DataObj
from data.board import Point
from data.cursor_board import Color
from datetime import datetime


class InstalledBomb(DataObj):
    color: Color
    position: Point
    explosion_range: int
    active_at: datetime
    active_at_mono: float
