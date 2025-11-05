from core.event import Event
from data.payload import IdPayload, ServerMessage, ClientMessage

from core.broker import EventBroker
from handler.connection import ConnectionHandler

QUIT = Event[IdPayload[str]]


@EventBroker.add_receiver("QUIT")
async def quit_receiver(event: QUIT):
    pass
