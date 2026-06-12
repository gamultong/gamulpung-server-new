from core.event import Event
from core.broker import EventBroker
from core.lifecycle import LifeCycle, RLife
from loguru import logger

from data.payload import IdDataPayload, ServerMessage, IdPayload
from data.cursor import Cursor
from data.board import PointRange
from data.event import InternalEvent, ServerEvent

from handler.cursor import CursorHandler
from handler.connection import ConnectionHandler

NOTIFY_CURSORS_EVENT = Event[IdPayload[str] | IdDataPayload[str, Cursor]]


@EventBroker.add_receiver(InternalEvent.NOTIFY_CURSORS)
@LifeCycle.with_async_lifecycle(factory=RLife.create_factory)
async def notify_cursors_receiver(event: NOTIFY_CURSORS_EVENT):
    id = event.payload.id
    try:
        cursor = await CursorHandler.get_by_id(id)
    except KeyError:
        logger.warning(f"커서가 존재하지 않음 | id:{id}")
        return
    range = PointRange(cursor.position, cursor.position)

    _event = Event(
        event_name=ServerEvent.CURSORS_STATE,
        payload=ServerMessage.CursorsState(
            [cursor]
        )
    )

    cursors = await CursorHandler.get_cursor_by_watching_range(range)
    targets = [cur.id for cur in cursors]

    await ConnectionHandler.multicast(targets, _event)
