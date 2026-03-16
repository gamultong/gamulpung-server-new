from enum import auto
from core.event import EventEnum


class ExternalEvent(EventEnum):
    __scope_part__ = "EXTERNAL"


class ClientEvent(ExternalEvent):
    __scope_part__ = "CLIENT"
    CHAT = auto()
    CREATE_CURSOR = auto()
    MOVE = auto()
    OPEN_TILES = auto()
    SET_FLAG = auto()
    SET_WINDOW = auto()
    DISMANTLE_MINE = auto()
    INSTALL_BOMB = auto()


class ServerEvent(ExternalEvent):
    __scope_part__ = "SERVER"
    CHAT = auto()
    CURSORS_STATE = auto()
    COLORED_TILES_STATE = auto()
    BOMB_POSITION = auto()
    EXPLOSION = auto()
    SCOREBOARD_STATE = auto()
    TILES_STATE = auto()
    MY_CURSOR = auto()
    QUIT_CURSOR = auto()
