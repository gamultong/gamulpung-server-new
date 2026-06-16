from core.event import Event
from core.broker import EventBroker
from core.lifecycle import LifeCycle, RLife

from data.payload import IdDataPayload, ClientMessage
from data.event import ClientEvent
from handler.cursor import CursorHandler
from loguru import logger

SET_WINDOW_EVENT = Event[IdDataPayload[str, ClientMessage.SetWindow]]


@EventBroker.add_receiver(ClientEvent.SET_WINDOW)
@LifeCycle.with_async_lifecycle(factory=RLife.create_factory)
async def set_window_receiver(event: SET_WINDOW_EVENT):
    id = event.payload.id
    data = event.payload.data

    # 기존 커서 조회 (반드시 존재해야 함)
    try:
        cursor = await CursorHandler.get_by_id(id)
    except KeyError:
        logger.error(f"윈도우 설정 실패: id {id}에 해당하는 커서를 찾을 수 없음")
        return

    # CursorHandler.set_window()가 viewport 업데이트 및 WINDOW_SET 이벤트 발행
    await CursorHandler.set_window(cursor, data.width, data.height)
