from core.event import Event
from data.payload import IdPayload, ServerMessage, ClientMessage
from data.event import TriggerEvent, ServerEvent

from core.broker import EventBroker
from handler.connection import ConnectionHandler
from handler.cursor import CursorHandler

QUIT = Event[IdPayload[str]]


@EventBroker.add_receiver(TriggerEvent.QUIT)
async def quit_receiver(event: QUIT):
    id = event.payload.id

    await CursorHandler.delete(id)

    _event = Event(
        event_name=ServerEvent.QUIT_CURSOR,
        payload=ServerMessage.QuitCursor(
            id=id
        )
    )

    await ConnectionHandler.broadcast(_event)
