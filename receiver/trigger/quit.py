from core.event import Event
from data.payload import IdPayload, ServerMessage, ClientMessage

from core.broker import EventBroker
from handler.connection import ConnectionHandler
from handler.cursor import CursorHandler

QUIT = Event[IdPayload[str]]


@EventBroker.add_receiver("QUIT")
async def quit_receiver(event: QUIT):
    id = event.payload.id

    # TODO: await CursorHandler.delete(id)

    _event = Event(
        event_name="QUIT-CURSOR",
        payload=ServerMessage.QuitCursor(
            id=id
        )
    )

    await ConnectionHandler.broadcast(_event)
