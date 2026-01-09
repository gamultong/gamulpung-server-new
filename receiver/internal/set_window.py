from core.event import Event
from core.broker import EventBroker
from core.lifecycle import LifeCycle, RLife

from data.payload import IdDataPayload, ServerMessage, IdPayload
from data.cursor import Cursor
from data.event import InternalEvent, ServerEvent

from handler.cursor import CursorHandler
from handler.connection import ConnectionHandler
from handler.board import BoardHandler

SET_WINDOW_EVENT = Event[IdDataPayload[str, Cursor] | IdPayload[str]]


@EventBroker.add_receiver(InternalEvent.SETTED_WINDOW)
@LifeCycle.with_async_lifecycle(factory=RLife.create_factory)
async def set_window_receiver(event: SET_WINDOW_EVENT):
    id = event.payload.id

    cursor = await CursorHandler.get_by_id(id)
    window_range = cursor.get_window_range()

    # 타일 정보 조회 및 전송
    tiles = await BoardHandler.fetch(window_range)

    elem = ServerMessage.TilesState.Elem(
        data=tiles.to_str(),
        range=window_range
    )

    tiles_event = Event(
        event_name=ServerEvent.TILES_STATE,
        payload=ServerMessage.TilesState(
            [elem]
        )
    )

    await ConnectionHandler.multicast([id], tiles_event)

    # 커서 정보 조회 및 전송
    cursors = await CursorHandler.get_cursors_by_cursor_window(cursor)

    cursors_event = Event(
        event_name=ServerEvent.CURSORS_STATE,
        payload=ServerMessage.CursorsState(
            cursors
        )
    )

    await ConnectionHandler.multicast([id], cursors_event)
