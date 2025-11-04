from core.event import Event
from core.broker import EventBroker

from data.payload import IdDataPayload, ServerMessage
from data.cursor import Cursor

from handler.cursor import CursorHandler
from handler.connection import ConnectionHandler

NOTIFY_CURSORS_EVENT = Event[IdDataPayload[str, Cursor]]


@EventBroker.add_receiver("NOTIFY-CURSORS")
async def notify_cursors_receiver(event: NOTIFY_CURSORS_EVENT):
    id = event.payload.id
    data = event.payload.data

    cursors = await CursorHandler.get_cursors_by_cursor_window(data)

    _event = Event(
        event_name="CURSORS-STATE",
        payload=ServerMessage.CursorsState(
            cursors
        )
    )

    await ConnectionHandler.multicast([id], _event)
