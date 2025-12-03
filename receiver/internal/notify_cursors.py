from core.event import Event
from core.broker import EventBroker

from data.payload import IdDataPayload, ServerMessage, IdPayload
from data.cursor import Cursor
from data.event import InternalEvent, ServerEvent

from handler.cursor import CursorHandler
from handler.connection import ConnectionHandler

NOTIFY_CURSORS_EVENT = Event[IdPayload[str] | IdDataPayload[str, Cursor]]


@EventBroker.add_receiver(InternalEvent.NOTIFY_CURSORS)
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
