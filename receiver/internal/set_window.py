from core.event import Event
from core.broker import EventBroker

from data.payload import IdDataPayload, ServerMessage, IdPayload
from data.cursor import Cursor

from handler.cursor import CursorHandler
from handler.connection import ConnectionHandler
from handler.board import BoardHandler

SET_WINDOW_EVENT = Event[IdDataPayload[str, Cursor] | IdPayload[str]]


@EventBroker.add_receiver("SETTED-WINDOW")
async def set_window_receiver(event: SET_WINDOW_EVENT):
    id = event.payload.id

    cursor = await CursorHandler.get_by_id(id)
    window_range = cursor.get_window_range()

    tiles = await BoardHandler.fetch(window_range)

    elem = ServerMessage.TilesState.Elem(
        data=tiles.to_str(),
        range=window_range
    )

    _event = Event(
        event_name="TILES-STATE",
        payload=ServerMessage.TilesState(
            [elem]
        )
    )

    await ConnectionHandler.multicast([id], _event)
