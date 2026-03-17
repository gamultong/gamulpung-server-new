from core.event import Event
from core.broker import EventBroker
from core.lifecycle import LifeCycle, RLife

from data.payload import IdDataPayload, ServerMessage
from data.board import PointRange
from data.bomb import InstalledBomb
from data.event import InternalEvent, ServerEvent

from handler.cursor import CursorHandler
from handler.connection import ConnectionHandler

INSTALLED_BOMB_EVENT = Event[IdDataPayload[str, InstalledBomb]]


@EventBroker.add_receiver(InternalEvent.INSTALLED_BOMB)
@LifeCycle.with_async_lifecycle(factory=RLife.create_factory)
async def installed_bomb_receiver(event: INSTALLED_BOMB_EVENT):
    bomb = event.payload.data
    point = bomb.position

    watching_cursors = await CursorHandler.get_cursor_by_watching_range(
        PointRange(point, point)
    )

    bomb_installed_event = Event(
        event_name=ServerEvent.BOMB_POSITION,
        payload=ServerMessage.BombPosition(
            color=int(bomb.color),
            position=point
        )
    )
    await ConnectionHandler.multicast([cur.id for cur in watching_cursors], bomb_installed_event)
