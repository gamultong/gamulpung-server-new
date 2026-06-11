from core.event import Event
from data.payload import IdDataPayload, ClientMessage
from data.event import ServerEvent, ClientEvent

from core.broker import EventBroker
from core.lifecycle import LifeCycle, RLife
from handler.board import BoardHandler
from handler.cursor import CursorHandler
from utils.stats import record_stat_event
from loguru import logger

SET_FLAG_EVENT = Event[IdDataPayload[str, ClientMessage.SetFlag]]


@EventBroker.add_receiver(ClientEvent.SET_FLAG)
@LifeCycle.with_async_lifecycle(factory=RLife.create_factory)
async def set_flag_receiver(event: SET_FLAG_EVENT):
    id = event.payload.id
    data = event.payload.data
    point = data.position

    cursor = await CursorHandler.get_by_id(id)
    if not cursor.is_alive:
        logger.warning(f"커서가 이미 사망함 | cursor:{cursor}")
        return

    # 깃발 설치 가능 범위 밖
    if not cursor.in_interaction_range(point):
        logger.warning(f"깃발 설치 가능 범위 밖으로 이동하려함 | cursor:{cursor}, point:{point}")
        return

    await BoardHandler.togle_flag(point)

    await CursorHandler.increase_score(cursor, 10)
    await record_stat_event(
        "SET_FLAG",
        actor_id=id,
        point=point,
        value=1,
        payload={"score_delta": 10},
    )
