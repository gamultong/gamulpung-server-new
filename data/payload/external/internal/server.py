from .base import ServerMessage
from core.dataobj import DataObj
from data.cursor import Cursor
from data.board import PointRange, Point


class Chat(ServerMessage):
    id: str
    message: str


class MyCursor(ServerMessage):
    id: str


class CursorsState(ServerMessage):
    cursors: list[Cursor]


class TilesState(ServerMessage):
    class Elem(DataObj):
        data: str
        range: PointRange

    tiles_li: list[Elem]


class Explosion(ServerMessage):
    position: Point
