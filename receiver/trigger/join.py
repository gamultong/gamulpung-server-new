from core.event import Event
from data.payload import IdPayload, ServerMessage, ClientMessage
from data.event import TriggerEvent, ServerEvent
from data.cursor import RankRange

from core.broker import EventBroker
from core.lifecycle import LifeCycle, RLife
from handler.connection import ConnectionHandler
from handler.cursor import CursorHandler
from utils.stats import record_stat_event

JOIN = Event[IdPayload[str]]


@EventBroker.add_receiver(TriggerEvent.JOIN)
@LifeCycle.with_async_lifecycle(factory=RLife.create_factory)
async def join_receiver(event: JOIN):
    id = event.payload.id

    cursors = await CursorHandler.get_cursor_by_rank_range(
        RankRange(1, 10)
    )
    scoreboard = {
        id: cursor.score
        for id, cursor in cursors.iter()
    }

    payload = ServerMessage.ScoreBoardState(
        scoreboard=scoreboard
    )
    _event = Event(
        event_name=ServerEvent.SCOREBOARD_STATE,
        payload=payload
    )

    await ConnectionHandler.multicast(
        target_ids=[id],
        event=_event
    )
    await record_stat_event(
        "JOIN",
        actor_id=id,
        value=1,
        payload={
            "connection_count": len(ConnectionHandler.conn_dict),
        },
    )
