from core.event import Event
from core.broker import EventBroker
from core.lifecycle import LifeCycle, RLife

from data.payload import IdDataPayload
from data.bomb import InstalledBomb
from data.event import TriggerEvent
from handler.cursor_board.internal.cursor_board import CursorBoardHandler


DRAW_BOARD_EVENT = Event[IdDataPayload[str, InstalledBomb]]


@EventBroker.add_receiver(TriggerEvent.DRAW_BOARD)
@LifeCycle.with_async_lifecycle(factory=RLife.create_factory)
async def draw_board_receiver(event: DRAW_BOARD_EVENT):
    id = event.payload.id
    bomb = event.payload.data

    await CursorBoardHandler.draw_board(
        cur_id=id,
        point=bomb.position,
        draw_range=bomb.explosion_range,
    )
