from core.dataobj import DataObj
from data.board import Point
from datetime import datetime


class InstalledBomb(DataObj):
    cur_id: str
    position: Point
    explosion_range: int
    active_at: datetime
    active_at_mono: float
