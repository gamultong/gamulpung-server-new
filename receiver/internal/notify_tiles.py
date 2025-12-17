from core.event import Event
from core.broker import EventBroker

from data.payload import IdDataPayload, ServerMessage, IdPayload
from data.board import PointRange
from data.event import InternalEvent, ServerEvent

from handler.cursor import CursorHandler
from handler.connection import ConnectionHandler
from handler.board import BoardHandler

NOTIFY_TILES_EVENT = Event[IdPayload[PointRange]]


@EventBroker.add_receiver(InternalEvent.NOTIFY_TILES)
async def notify_tiles_receiver(event: NOTIFY_TILES_EVENT):
    point_range = event.payload.id
    tiles = await BoardHandler.fetch(point_range)

    cursors = await CursorHandler.get_cursor_by_watching_range(point_range)
    elem = ServerMessage.TilesState.Elem(
        data=tiles.to_str(),
        range=point_range
    )

    _event = Event(
        event_name=ServerEvent.TILES_STATE,
        payload=ServerMessage.TilesState(
            [elem]
        )
    )

    await ConnectionHandler.multicast([cur.id for cur in cursors], _event)
