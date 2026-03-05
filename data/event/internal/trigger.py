from enum import auto
from core.event import EventEnum

class TriggerEvent(EventEnum):
    __scope_part__ = "TRIGGER"
    JOIN = auto()
    QUIT = auto()
    DRAW_BOARD = auto()
