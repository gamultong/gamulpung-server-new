from loguru import logger

from core.event import Event
from core.broker import EventBroker
from core.lifecycle import LifeCycle, RLife

from data.payload import IdDataPayload, ClientMessage
from data.event import ClientEvent
from data.cursor import ItemType

from handler.board import BoardHandler
from handler.cursor import CursorHandler
from handler.stats import StatsHandler

from receiver.utils import chaining

DISMANTLE_MINE_EVENT = Event[IdDataPayload[str, ClientMessage.DismantleMine]]


@EventBroker.add_receiver(ClientEvent.DISMANTLE_MINE)
@LifeCycle.with_async_lifecycle(factory=RLife.create_factory)
async def dismantle_mine_receiver(event: DISMANTLE_MINE_EVENT):
    id = event.payload.id
    data = event.payload.data

    point = data.position

    cursor = await CursorHandler.get_by_id(id)
    if not cursor.is_alive:
        logger.warning(f"커서가 이미 사망함 | cursor:{cursor}")
        return
    if not cursor.in_interaction_range(point):
        logger.warning(f"상호작용 범위 밖 타일 지뢰 해체 시도 | cursor:{cursor}, point:{point}")
        return

    tile = await BoardHandler.fetch_tile(point)
    if not tile.is_flag:
        logger.warning(f"깃발이 설치되지 않은 타일 지뢰 해체 시도 | cursor:{cursor}, tile:{tile}")
        return
    if tile.is_open:
        logger.warning(f"열린 타일 지뢰 해체 시도 | cursor:{cursor}, tile:{tile}")
        return

    await BoardHandler.togle_flag(point)

    if tile.is_mine:
        await BoardHandler.dismantle_mine(point)
        # 지뢰 획득 로직
        await CursorHandler.grant_item(cursor, ItemType.BOMB, 1)
        await StatsHandler.record(
            "DISMANTLE_MINE",
            actor_id=id,
            point=point,
            value=1,
            payload={"item_type": ItemType.BOMB.value, "item_delta": 1},
        )
        return

    chaining_points = await chaining(point)
    for p in chaining_points:
        await BoardHandler.open_tiles(p)
        await StatsHandler.record(
            "OPEN_TILE",
            actor_id=id,
            point=p,
            value=1,
            payload={"source": "DISMANTLE_MINE", "is_mine": False},
        )
