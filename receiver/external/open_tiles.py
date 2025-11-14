from core.event import Event
from data.payload import IdDataPayload, ClientMessage

from core.broker import EventBroker
from handler.board import BoardHandler
from handler.cursor import CursorHandler

OPEN_TILES_EVENT = Event[IdDataPayload[str, ClientMessage.OpenTiles]]


@EventBroker.add_receiver("OPEN-TILES")
async def open_tiles_receiver(event: OPEN_TILES_EVENT):
    id = event.payload.id
    data = event.payload.data

    cursor = await CursorHandler.get_by_id(id)
    assert cursor.in_interaction_range(data.position)

    await BoardHandler.open_tiles(data.position)

    await CursorHandler.increase_score(cursor, 100)
