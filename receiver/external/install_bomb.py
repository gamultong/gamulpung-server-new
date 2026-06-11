from loguru import logger

from core.event import Event
from core.broker import EventBroker
from core.lifecycle import LifeCycle, RLife

from data.payload import IdDataPayload, ClientMessage
from data.event import ClientEvent
from data.cursor import ItemType
from handler.bomb import BombHandler
from handler.cursor import CursorHandler
from handler.stats import StatsHandler


INSTALL_BOMB_EVENT = Event[IdDataPayload[str, ClientMessage.InstallBomb]]


@EventBroker.add_receiver(ClientEvent.INSTALL_BOMB)
@LifeCycle.with_async_lifecycle(factory=RLife.create_factory)
async def install_bomb_receiver(event: INSTALL_BOMB_EVENT):
    id = event.payload.id
    data = event.payload.data

    point = data.position

    cursor = await CursorHandler.get_by_id(id)
    if not cursor.is_alive:
        logger.warning(f"커서가 이미 사망함 | cursor:{cursor}")
        return
    if not cursor.in_interaction_range(point):
        logger.warning(f"상호작용 범위 밖 타일 폭탄 설치 시도 | cursor:{cursor}, point:{point}")
        return
    if cursor.items.bomb <= 0:
        logger.warning(f"폭탄을 가지고 있지 않은 커서가 폭탄 설치 시도 | cursor:{cursor}, bomb:{cursor.items.bomb}")
        return

    await CursorHandler.grant_item(cursor, ItemType.BOMB, -1)

    await BombHandler.install_bomb(cursor.id, point)
    await StatsHandler.record(
        "INSTALL_BOMB",
        actor_id=id,
        point=point,
        value=1,
        payload={"item_type": ItemType.BOMB.value, "item_delta": -1},
    )
