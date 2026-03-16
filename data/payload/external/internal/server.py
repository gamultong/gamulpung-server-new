from .base import ServerMessage
from core.dataobj import DataObj
from data.cursor import Cursor
from data.board import PointRange, Point


class Chat(ServerMessage):
    id: str
    message: str


class MyCursor(ServerMessage):
    id: str


class QuitCursor(ServerMessage):
    id: str


class CursorsState(ServerMessage):
    cursors: list[Cursor]


class TilesState(ServerMessage):
    class Elem(DataObj):
        data: str
        range: PointRange

    tiles_li: list[Elem]


class ColoredTilesState(ServerMessage):
    class Elem(DataObj):
        my_tiles_data: str
        colored_tiles_data: str
        range: PointRange

    colored_tiles_li: list[Elem]


class BombPosition(ServerMessage):
    color: int
    position: Point


class Explosion(ServerMessage):
    position: Point


class ScoreBoardState(ServerMessage):
    scoreboard: dict[int, int]
