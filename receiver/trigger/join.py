from core.event import Event
from data.payload import IdPayload, ServerMessage, ClientMessage
from data.event import TriggerEvent, ServerEvent

from core.broker import EventBroker
from handler.connection import ConnectionHandler

JOIN = Event[IdPayload[str]]


@EventBroker.add_receiver(TriggerEvent.JOIN)
async def join_receiver(event: JOIN):
    id = event.payload.id

    payload = ServerMessage.MyCursor(
        id=id,
    )

    # 이름 중복으로 하면 pylance가 지랄함
    _event = Event(
        event_name=ServerEvent.MY_CURSOR,
        payload=payload
    )

    await ConnectionHandler.multicast(
        target_ids=[id],
        event=_event
    )
