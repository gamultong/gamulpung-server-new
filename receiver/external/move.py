from core.event import Event
from core.broker import EventBroker

from data.payload import IdDataPayload, ClientMessage, IdPayload
from data.cursor import Cursor

from handler.cursor import CursorHandler
from handler.board import BoardHandler

MOVE_EVENT = Event[IdDataPayload[str, ClientMessage.Move]]


@EventBroker.add_receiver("MOVE")
async def move_receiver(event: MOVE_EVENT):
    id = event.payload.id
    data = event.payload.data

    target_tile = await BoardHandler.fetch_point(data.position)
    assert target_tile.is_open

    cursor = await CursorHandler.get_by_id(id)
    cursor.position = data.position

    await CursorHandler.move(cursor)
