from .base import ServerMessage


class Chat(ServerMessage):
    id: str
    message: str


class MyCursor(ServerMessage):
    id: str
