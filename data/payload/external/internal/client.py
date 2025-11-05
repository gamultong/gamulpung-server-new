from .base import ClientMessage


class Chat(ClientMessage):
    message: str


class SetWindow(ClientMessage):
    width: int
    height: int
