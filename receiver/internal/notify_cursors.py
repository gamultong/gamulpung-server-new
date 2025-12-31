from core.event import Event
from core.broker import EventBroker
from core.lifecycle import LifeCycle, RLife

from data.payload import IdDataPayload, ServerMessage, IdPayload
from data.cursor import Cursor
from data.event import InternalEvent, ServerEvent

from handler.cursor import CursorHandler
from handler.connection import ConnectionHandler

NOTIFY_CURSORS_EVENT = Event[IdPayload[str] | IdDataPayload[str, Cursor]]


@EventBroker.add_receiver(InternalEvent.NOTIFY_CURSORS)
@LifeCycle.with_async_lifecycle(factory=RLife.create_factory)
async def notify_cursors_receiver(event: NOTIFY_CURSORS_EVENT):
    id = event.payload.id
    cursor = await CursorHandler.get_by_id(id)

    cursors = await CursorHandler.get_cursors_by_cursor_window(cursor)

    _event = Event(
        event_name=ServerEvent.CURSORS_STATE,
        payload=ServerMessage.CursorsState(
            cursors
        )
    )

    await ConnectionHandler.multicast([id], _event)
