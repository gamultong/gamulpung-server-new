from .base import ServerMessage
from data.cursor import Cursor


class Chat(ServerMessage):
    id: str
    message: str


class MyCursor(ServerMessage):
    id: str


class CursorsState(ServerMessage):
    cursors: list[Cursor]
