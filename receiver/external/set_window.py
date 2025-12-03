from core.event import Event
from core.broker import EventBroker

from data.payload import IdDataPayload, ClientMessage, IdPayload
from data.cursor import Cursor
from data.event import ServerEvent, ClientEvent

from handler.cursor import CursorHandler

SET_WINDOW_EVENT = Event[IdDataPayload[str, ClientMessage.SetWindow]]


@EventBroker.add_receiver(ClientEvent.SET_WINDOW)
async def set_window_receiver(event: SET_WINDOW_EVENT):
    id = event.payload.id
    data = event.payload.data

    cursor = Cursor.create(
        id=id,
        width=data.width,
        height=data.height
    )

    await CursorHandler.create(cursor)
