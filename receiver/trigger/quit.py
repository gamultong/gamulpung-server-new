from core.event import Event
from data.payload import IdPayload, ServerMessage, ClientMessage
from data.event import TriggerEvent, ServerEvent

from core.broker import EventBroker
from core.lifecycle import LifeCycle, RLife
from handler.connection import ConnectionHandler
from handler.cursor import CursorHandler
from handler.stats import StatsHandler

QUIT = Event[IdPayload[str]]


@EventBroker.add_receiver(TriggerEvent.QUIT)
@LifeCycle.with_async_lifecycle(factory=RLife.create_factory)
async def quit_receiver(event: QUIT):
    id = event.payload.id

    point = None
    had_cursor = False
    try:
        cursor = await CursorHandler.get_by_id(id)
        point = cursor.position
        had_cursor = True
    except KeyError:
        pass

    await CursorHandler.delete(id)

    _event = Event(
        event_name=ServerEvent.QUIT_CURSOR,
        payload=ServerMessage.QuitCursor(
            id=id
        )
    )

    await ConnectionHandler.broadcast(_event)
    await StatsHandler.record(
        "QUIT",
        actor_id=id,
        point=point,
        value=1,
        payload={
            "connection_count": len(ConnectionHandler.conn_dict),
            "had_cursor": had_cursor,
        },
    )
