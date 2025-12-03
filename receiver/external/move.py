from core.event import Event
from core.broker import EventBroker

from data.payload import IdDataPayload, ClientMessage, IdPayload
from data.cursor import Cursor
from data.event import ServerEvent, ClientEvent

from handler.cursor import CursorHandler
from handler.board import BoardHandler

MOVE_EVENT = Event[IdDataPayload[str, ClientMessage.Move]]


@EventBroker.add_receiver(ClientEvent.MOVE)
async def move_receiver(event: MOVE_EVENT):
    id = event.payload.id
    data = event.payload.data

    target_tile = await BoardHandler.fetch_tile(data.position)
    assert target_tile.is_open

    cursor = await CursorHandler.get_by_id(id)

    await CursorHandler.move(cursor, data.position)
