from core.event import Event
from data.payload import IdDataPayload, ClientMessage

from core.broker import EventBroker
from handler.board import BoardHandler
from handler.cursor import CursorHandler

SET_FLAG_EVENT = Event[IdDataPayload[str, ClientMessage.SetFlag]]


@EventBroker.add_receiver("SET-FLAG")
async def set_flag_receiver(event: SET_FLAG_EVENT):
    id = event.payload.id
    data = event.payload.data

    cursor = await CursorHandler.get_by_id(id)
    assert cursor.in_interaction_range(data.position)

    await BoardHandler.togle_flag(data.position)
