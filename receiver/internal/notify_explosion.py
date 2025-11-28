from core.event import Event, InternalEvent, ExternalS2CEvent
from core.broker import EventBroker

from data.payload import IdDataPayload, ServerMessage, IdPayload
from data.board import PointRange, Tiles, Tile, Point

from handler.cursor import CursorHandler
from handler.connection import ConnectionHandler
from handler.board import BoardHandler
from datetime import datetime, timedelta

NOTIFY_EXPLOSION_EVENT = Event[IdDataPayload[Point, Tile]]


@EventBroker.add_receiver(InternalEvent.NOTIFY_EXPLOSION)
async def notify_explosion_receiver(event: NOTIFY_EXPLOSION_EVENT):
    point = event.payload.id
    point_range = PointRange.create_by_mid(point, 1, 1)
    explosion_cursors = await CursorHandler.get_cursor_in_range(point_range)
    watching_cursors = await CursorHandler.get_cursor_by_watching_range(PointRange(point, point))

    for cursor in explosion_cursors:
        await CursorHandler.death(cursor)

    _event = Event(
        event_name=ExternalS2CEvent.EXPLOSION,
        payload=ServerMessage.Explosion(
            point
        )
    )

    await ConnectionHandler.multicast([cur.id for cur in watching_cursors], _event)
