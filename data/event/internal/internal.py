from enum import auto
from core.event import EventEnum


class InternalEvent(EventEnum):
    __scope_part__ = "INTERNAL"
    NOTIFY_CURSORS = auto()
    NOTIFY_EXPLOSION = auto()
    NOTIFY_SCOREBOARD = auto()
    NOTIFY_TILES = auto()
    SETTED_WINDOW = auto()
    CREATED = auto()
