from core.event import Event
from core.broker import EventBroker
from core.lifecycle import LifeCycle, RLife

from data.payload import IdDataPayload, ClientMessage
from data.event import ClientEvent

from handler.cursor import CursorHandler
from handler.board import BoardHandler
from loguru import logger

MOVE_EVENT = Event[IdDataPayload[str, ClientMessage.Move]]


@EventBroker.add_receiver(ClientEvent.MOVE)
@LifeCycle.with_async_lifecycle(factory=RLife.create_factory)
async def move_receiver(event: MOVE_EVENT):
    id = event.payload.id
    data = event.payload.data
    point = data.position

    cursor = await CursorHandler.get_by_id(id)
    if not cursor.is_alive:
        logger.warning(f"커서가 이미 사망함 | cursor:{cursor}")
        return

    target_tile = await BoardHandler.fetch_tile(point)
    # 닫힌 타일
    if not target_tile.is_open:
        logger.warning(f"닫힌 타일로 이동하려함 | cursor:{cursor}, tile:{target_tile}, point:{point}")
        return

    # 이동 가능 범위 밖
    if not cursor.in_interaction_range(point):
        logger.warning(f"이동 가능 범위 밖으로 이동하려함 | cursor:{cursor}, tile:{target_tile}, point:{point}")
        return
    # 재자리 이동
    if cursor.position == point:
        logger.warning(f"재자리로 이동하려함 | cursor:{cursor}, tile:{target_tile}, point:{point}")
        return

    await CursorHandler.move(cursor, point)
