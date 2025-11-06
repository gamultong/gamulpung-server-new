from .base import ClientMessage
from data.board import Point


class Chat(ClientMessage):
    message: str


class SetWindow(ClientMessage):
    width: int
    height: int


class Move(ClientMessage):
    position: Point


class OpenTiles(ClientMessage):
    position: Point
