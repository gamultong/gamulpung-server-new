from core.event import Event
from data.payload import IdDataPayload, ServerMessage, ClientMessage
from data.event import ServerEvent, ClientEvent

from core.broker import EventBroker
from handler.connection import ConnectionHandler
from handler.cursor import CursorHandler

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

    # 발신자의 cursor 조회
    sender_cursor = await CursorHandler.get_by_id(id)

    # 발신자의 시야 범위 내 커서들 조회
    cursors_in_view = await CursorHandler.get_cursors_by_cursor_window(sender_cursor)

    # 시야 범위 내 사용자 ID 추출
    target_ids = [cursor.id for cursor in cursors_in_view]

    # multicast (시야 범위 내 사용자에게만 전송)
    await ConnectionHandler.multicast(target_ids, _event)
