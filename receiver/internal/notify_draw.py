from core.event import Event
from core.broker import EventBroker
from core.lifecycle import LifeCycle, RLife

from data.payload import IdPayload, ServerMessage
from data.board import PointRange
from data.event import InternalEvent, ServerEvent

from handler.cursor import CursorHandler
from handler.connection import ConnectionHandler
from handler.cursor_board import CursorBoardHandler


NOTIFY_DRAW_EVENT = Event[IdPayload[PointRange]]


@EventBroker.add_receiver(InternalEvent.NOTIFY_DRAW)
@LifeCycle.with_async_lifecycle(factory=RLife.create_factory)
async def notify_draw_receiver(event: NOTIFY_DRAW_EVENT):
    point_range = event.payload.id
    cursors = await CursorHandler.get_cursor_by_watching_range(point_range)
    targets = [cur.id for cur in cursors]

    cursor_tiles = await CursorBoardHandler.fetch(point_range)
    colored_tiles_data = await CursorHandler.to_colored_tiles_data(cursor_tiles)
    colored_tiles_li = [
        ServerMessage.ColoredTilesState.Elem(
            data=colored_tiles_data,
            range=point_range
        )
    ]

    colored_tiles_event = Event(
        event_name=ServerEvent.COLORED_TILES_STATE,
        payload=ServerMessage.ColoredTilesState(colored_tiles_li=colored_tiles_li)
    )

    await ConnectionHandler.multicast(targets, colored_tiles_event)
