from .base import ClientMessage
from data.board import Point
from data.cursor_board import Color


class Chat(ClientMessage):
    message: str


class CreateCursor(ClientMessage):
    width: int
    height: int
    color: int

    @classmethod
    def from_dict(cls, dict: dict):
        if "color" not in dict:
            raise ValueError("CREATE_CURSOR payload에 color가 필요합니다.")

        return cls(
            width=dict["width"],
            height=dict["height"],
            color=int(dict["color"]),
        )


class SetWindow(ClientMessage):
    width: int
    height: int


class Move(ClientMessage):
    position: Point


class OpenTiles(ClientMessage):
    position: Point


class SetFlag(ClientMessage):
    position: Point


class DismantleMine(ClientMessage):
    position: Point


class InstallBomb(ClientMessage):
    position: Point
