from core.event import Event
from core.broker import EventBroker
from core.lifecycle import LifeCycle, RLife

from data.payload import IdDataPayload, ServerMessage, IdPayload
from data.board import PointRange
from data.event import InternalEvent, ServerEvent

from handler.cursor import CursorHandler
from handler.connection import ConnectionHandler
from handler.board import BoardHandler

NOTIFY_TILES_EVENT = Event[IdPayload[PointRange]]


@EventBroker.add_receiver(InternalEvent.NOTIFY_TILES)
@LifeCycle.with_async_lifecycle(factory=RLife.create_factory)
async def notify_tiles_receiver(event: NOTIFY_TILES_EVENT):
    from loguru import logger

    point_range = event.payload.id
    tiles = await BoardHandler.fetch(point_range)

    cursors = await CursorHandler.get_cursor_by_watching_range(point_range)

    logger.debug(
        f"notify_tiles_receiver: point_range={point_range}, "
        f"cursors_count={len(cursors)}, "
        f"cursor_ids={[c.id for c in cursors]}"
    )

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
