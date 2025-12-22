from core.event import Event
from data.payload import IdPayload, ServerMessage, ClientMessage
from data.event import TriggerEvent, ServerEvent
from data.cursor import RankRange

from core.broker import EventBroker
from handler.connection import ConnectionHandler
from handler.cursor import CursorHandler

JOIN = Event[IdPayload[str]]


@EventBroker.add_receiver(TriggerEvent.JOIN)
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
