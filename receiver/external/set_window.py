from core.event import Event
from core.broker import EventBroker

from data.payload import IdDataPayload, ClientMessage, IdPayload
from data.cursor import Cursor

from handler.cursor import CursorHandler

SET_WINDOW_EVENT = Event[IdDataPayload[str, ClientMessage.SetWindow] | IdPayload[str]]


@EventBroker.add_receiver("SET-WINDOW")
async def set_windwo_receiver(event: SET_WINDOW_EVENT):
    id = event.payload.id

    # Handle both IdDataPayload (from client) and IdPayload (from internal trigger)
    if hasattr(event.payload, 'data'):
        data = event.payload.data

        cursor = Cursor.create(
            id=id,
            width=data.width,
            height=data.height
        )

        await CursorHandler.create(cursor)
