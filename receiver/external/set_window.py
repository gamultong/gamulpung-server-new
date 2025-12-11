from core.event import Event
from core.broker import EventBroker

from data.payload import IdDataPayload, ClientMessage, IdPayload
from data.event import ClientEvent, InternalEvent
from handler.cursor import CursorHandler
from loguru import logger

SET_WINDOW_EVENT = Event[IdDataPayload[str, ClientMessage.SetWindow]]


@EventBroker.add_receiver(ClientEvent.SET_WINDOW)
async def set_window_receiver(event: SET_WINDOW_EVENT):
    id = event.payload.id
    data = event.payload.data

    # 기존 커서 조회 (반드시 존재해야 함)
    try:
        cursor = await CursorHandler.get_by_id(id)
    except KeyError:
        logger.error(f"윈도우 설정 실패: id {id}에 해당하는 커서를 찾을 수 없음")
        return

    # viewport 크기만 업데이트
    cursor.width = data.width
    cursor.height = data.height

    await CursorHandler.update(cursor)

    # viewport 업데이트 내부 이벤트 발행
    await EventBroker.publish(
        Event(
            event_name=InternalEvent.SETTED_WINDOW,
            payload=IdPayload(id=id)
        )
    )
