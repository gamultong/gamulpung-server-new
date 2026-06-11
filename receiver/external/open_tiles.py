from loguru import logger

from core.event import Event
from core.broker import EventBroker
from core.lifecycle import LifeCycle, RLife

from data.payload import IdDataPayload, ClientMessage
from data.event import ClientEvent

from handler.board import BoardHandler
from handler.cursor import CursorHandler
from utils.stats import record_stat_event

from receiver.utils import chaining

OPEN_TILES_EVENT = Event[IdDataPayload[str, ClientMessage.OpenTiles]]


@EventBroker.add_receiver(ClientEvent.OPEN_TILES)
@LifeCycle.with_async_lifecycle(factory=RLife.create_factory)
async def open_tiles_receiver(event: OPEN_TILES_EVENT):
    id = event.payload.id
    data = event.payload.data

    point = data.position

    cursor = await CursorHandler.get_by_id(id)
    if not cursor.is_alive:
        logger.warning(f"커서가 이미 사망함 | cursor:{cursor}")
        return
    if not cursor.in_interaction_range(point):
        logger.warning(f"상호작용 범위 밖 타일 열람 시도 | cursor:{cursor}, point:{point}")
        return

    tile = await BoardHandler.fetch_tile(point)
    if tile.is_flag:
        logger.warning(f"깃발이 설치된 타일 열람 시도 | cursor:{cursor}, tile:{tile}")
        return
    if tile.is_open:
        logger.warning(f"열린 타일 열람 시도 | cursor:{cursor}, tile:{tile}")
        return
    if tile.is_mine:
        await BoardHandler.open_tiles(point)
        await record_stat_event(
            "OPEN_TILE",
            actor_id=id,
            point=point,
            value=1,
            payload={"is_mine": True},
        )
        return

    chaining_points = await chaining(point)
    for p in chaining_points:
        await BoardHandler.open_tiles(p)
        await CursorHandler.increase_score(cursor, 100)
        await record_stat_event(
            "OPEN_TILE",
            actor_id=id,
            point=p,
            value=1,
            payload={"is_mine": False, "score_delta": 100},
        )
    # await BoardHandler.open_tiles(point)
    # await CursorHandler.increase_score(cursor, 100)
