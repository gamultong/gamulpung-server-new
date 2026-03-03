from core.event import Event
from core.broker import EventBroker
from core.lifecycle import LifeCycle, RLife

from data.payload import IdDataPayload, ServerMessage, IdPayload
from data.board import PointRange, Tiles, Point
from data.bomb import ExplosionInfo
from data.event import InternalEvent, ServerEvent

from handler.cursor import CursorHandler
from handler.connection import ConnectionHandler
from handler.board import BoardHandler
from datetime import datetime, timedelta

NOTIFY_EXPLOSION_EVENT = Event[IdDataPayload[Point, ExplosionInfo]]


@EventBroker.add_receiver(InternalEvent.NOTIFY_EXPLOSION)
@LifeCycle.with_async_lifecycle(factory=RLife.create_factory)
async def notify_explosion_receiver(event: NOTIFY_EXPLOSION_EVENT):
    point = event.payload.id
    explosion_range = event.payload.data.explosion_range
    point_range = PointRange.create_by_mid(point, explosion_range, explosion_range)
    explosion_cursors = await CursorHandler.get_cursor_in_range(point_range)
    watching_cursors = await CursorHandler.get_cursor_by_watching_range(PointRange(point, point))

    for cursor in explosion_cursors:
        await CursorHandler.death(cursor)

    _event = Event(
        event_name=ServerEvent.EXPLOSION,
        payload=ServerMessage.Explosion(
            point
        )
    )

    await ConnectionHandler.multicast([cur.id for cur in watching_cursors], _event)
