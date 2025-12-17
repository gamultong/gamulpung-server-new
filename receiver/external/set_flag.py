from core.event import Event
from data.payload import IdDataPayload, ClientMessage
from data.event import ServerEvent, ClientEvent

from core.broker import EventBroker
from handler.board import BoardHandler
from handler.cursor import CursorHandler
from loguru import logger

SET_FLAG_EVENT = Event[IdDataPayload[str, ClientMessage.SetFlag]]


@EventBroker.add_receiver(ClientEvent.SET_FLAG)
async def set_flag_receiver(event: SET_FLAG_EVENT):
    id = event.payload.id
    data = event.payload.data

    cursor = await CursorHandler.get_by_id(id)
    if not cursor.is_alive:
        logger.warning(f"커서가 이미 사망함 | cursor:{cursor}")
        return
    assert cursor.in_interaction_range(data.position)

    await BoardHandler.togle_flag(data.position)

    await CursorHandler.increase_score(cursor, 10)
