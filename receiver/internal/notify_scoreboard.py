from core.event import Event, InternalEvent, ExternalS2CEvent
from core.broker import EventBroker

from data.payload import IdDataPayload, ServerMessage, IdPayload
from data.cursor import Cursor, RankRange, CursorRankRange

from handler.cursor import CursorHandler
from handler.connection import ConnectionHandler

NOTIFY_SCOREBOARD_EVENT = Event[IdDataPayload[RankRange, CursorRankRange]]


@EventBroker.add_receiver(InternalEvent.NOTIFY_SCOREBOARD)
async def notify_scoreboard_receiver(event: NOTIFY_SCOREBOARD_EVENT):
    range = event.payload.id

    cur_rank_range = await CursorHandler.get_cursor_by_rank_range(range)

    _event = Event(
        event_name=ExternalS2CEvent.SCOREBOARD_STATE,
        payload=ServerMessage.ScoreBoardState(
            {idx+1: c.score for idx, c in enumerate(cur_rank_range.cursors)}
        )
    )

    await ConnectionHandler.broadcast(_event)
