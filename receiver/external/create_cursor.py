from core.event import Event
from core.broker import EventBroker
from core.lifecycle import LifeCycle, RLife

from data.payload import IdDataPayload, ClientMessage, ServerMessage
from data.cursor import Cursor
from data.event import ServerEvent, ClientEvent
from data.board import Point
from data.cursor_board import Color

from handler.cursor import CursorHandler
from handler.connection import ConnectionHandler
from loguru import logger

CREATE_CURSOR_EVENT = Event[IdDataPayload[str, ClientMessage.CreateCursor]]


@EventBroker.add_receiver(ClientEvent.CREATE_CURSOR)
@LifeCycle.with_async_lifecycle(factory=RLife.create_factory)
async def create_cursor_receiver(event: CREATE_CURSOR_EVENT):
    id = event.payload.id
    data = event.payload.data

    # 커서 중복 생성 방지
    try:
        await CursorHandler.get_by_id(id)
        logger.warning(f"커서 중복 생성 시도: id {id}에 대한 커서가 이미 존재함")
        return
    except KeyError:
        pass  # 새 커서인 경우 정상

    try:
        color = Color(data.color)
    except ValueError:
        logger.warning(f"유효하지 않은 color 값: id={id}, color={data.color}")
        return

    # 클라이언트가 제공한 window 크기와 color로 커서 생성
    cursor = Cursor.create(
        id=id,
        position=Point(0, 0),  # 항상 (0, 0)에서 시작
        width=data.width,
        height=data.height,
        color=color,
    )

    # MY_CURSOR 이벤트 전송 (클라이언트에게 cursor ID 알림)
    await ConnectionHandler.multicast(
        target_ids=[id],
        event=Event(
            event_name=ServerEvent.MY_CURSOR,
            payload=ServerMessage.MyCursor(id=id)
        )
    )

    # 핸들러에 저장 (CursorHandler.create가 자동으로 NOTIFY_CURSORS를 통해 CURSORS_STATE 발행)
    await CursorHandler.create(cursor)
