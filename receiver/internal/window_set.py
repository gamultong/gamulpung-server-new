from core.event import Event
from core.broker import EventBroker
from core.lifecycle import LifeCycle, RLife
from loguru import logger

from data.payload import IdDataPayload, ServerMessage, IdPayload
from data.cursor import Cursor
from data.event import InternalEvent, ServerEvent

from handler.cursor import CursorHandler
from handler.connection import ConnectionHandler
from handler.board import BoardHandler
from handler.cursor_board import CursorBoardHandler

WINDOW_SET_EVENT = Event[IdDataPayload[str, Cursor] | IdPayload[str]]


@EventBroker.add_receiver(InternalEvent.WINDOW_SET)
@LifeCycle.with_async_lifecycle(factory=RLife.create_factory)
async def window_set_receiver(event: WINDOW_SET_EVENT):
    id = event.payload.id

    try:
        cursor = await CursorHandler.get_by_id(id)
    except KeyError:
        logger.warning(f"커서가 존재하지 않음 | id:{id}")
        return
    window_range = cursor.get_window_range()

    # 타일 정보 조회 및 전송 (닫힌 타일의 mine·number는 클라이언트에 노출하지 않는다)
    tiles = await BoardHandler.fetch(window_range)

    elem = ServerMessage.TilesState.Elem(
        data=tiles.hide_info().to_str(),
        range=window_range
    )

    tiles_event = Event(
        event_name=ServerEvent.TILES_STATE,
        payload=ServerMessage.TilesState(
            [elem]
        )
    )

    await ConnectionHandler.multicast([id], tiles_event)

    cursor_tiles = await CursorBoardHandler.fetch(window_range)
    my_tiles_data = await CursorHandler.to_my_tiles_data(cursor_tiles, id)
    colored_tiles_data = await CursorHandler.to_colored_tiles_data(cursor_tiles)
    colored_tiles_li = [
        ServerMessage.ColoredTilesState.Elem(
            my_tiles_data=my_tiles_data,
            colored_tiles_data=colored_tiles_data,
            range=window_range
        )
    ]

    colored_tiles_event = Event(
        event_name=ServerEvent.COLORED_TILES_STATE,
        payload=ServerMessage.ColoredTilesState(colored_tiles_li=colored_tiles_li)
    )

    await ConnectionHandler.multicast([id], colored_tiles_event)

    # 커서 정보 조회 및 전송
    cursors = await CursorHandler.get_cursors_by_cursor_window(cursor)

    cursors_event = Event(
        event_name=ServerEvent.CURSORS_STATE,
        payload=ServerMessage.CursorsState(
            cursors
        )
    )

    await ConnectionHandler.multicast([id], cursors_event)
