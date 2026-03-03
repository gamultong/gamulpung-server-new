from __future__ import annotations

from core.dataobj import DataObj
from data.board import Tile


class ExplosionInfo(DataObj):
    tile: Tile
    explosion_range: int
