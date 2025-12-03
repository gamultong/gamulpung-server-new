from core.event import Event
from data.payload import IdDataPayload, ServerMessage, ClientMessage
from data.event import ServerEvent, ClientEvent

from core.broker import EventBroker
from handler.connection import ConnectionHandler

CHAT_EVENT = Event[IdDataPayload[str, ClientMessage.Chat]]


@EventBroker.add_receiver(ClientEvent.CHAT)
async def chat_receiver(event: CHAT_EVENT):
    id = event.payload.id
    data = event.payload.data

    payload = ServerMessage.Chat(
        id=id,
        message=data.message
    )

    # 이름 중복으로 하면 pylance가 지랄함
    _event = Event(
        event_name=ServerEvent.CHAT,
        payload=payload
    )

    # TODO: 현재는 broadcast, 이후 커서 시아에 포함되는 녀석에게만 multicast
    await ConnectionHandler.broadcast(_event)
