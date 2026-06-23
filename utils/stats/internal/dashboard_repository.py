from __future__ import annotations

from collections import Counter, defaultdict
from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass, field, replace
from datetime import datetime, timedelta, timezone
import json

from handler.board.storage import DB
from utils.logging import (
    get_latest_join_times,
    get_previous_connection_payloads,
    get_recent_app_logs,
    get_recent_stat_events,
    get_stat_event_observed_range,
    get_stat_events_since,
    get_total_stat_event_count,
)
from utils.logging.internal.repository import JsonObject, JsonValue

DEFAULT_RANGE_VALUE = "all"
DEFAULT_BUCKET = "1m"
DEFAULT_LIMIT = 50
MIN_LIMIT = 1
MAX_LIMIT = 200
PREVIOUS_CONNECTION_LOOKBACK_LIMIT = 20
TOP_PLAYERS_LIMIT = 20
TOP_TILES_LIMIT = 20
ALL_EVENTS_SINCE = "0001-01-01T00:00:00.000000Z"
ALL_RANGE_VALUE = "all"

MINUTE_BUCKET = "1m"
FIVE_MINUTE_BUCKET = "5m"
FIVE_MINUTE_BUCKET_SIZE = 5
HOUR_BUCKET = "1h"
DEFAULT_RANGE_AMOUNT = 24
MINUTES_UNIT = "m"
DAYS_UNIT = "d"
HOURS_UNIT = "h"

JOIN_EVENT = "JOIN"
QUIT_EVENT = "QUIT"
CREATE_CURSOR_EVENT = "CREATE_CURSOR"
MOVE_EVENT = "MOVE"
OPEN_TILE_EVENT = "OPEN_TILE"
SET_FLAG_EVENT = "SET_FLAG"
EXPLOSION_EVENT = "EXPLOSION"
DEBUG_LEVEL = "DEBUG"
SCORE_CHANGE_EVENT = "SCORE_CHANGE"
TILE_HEATMAP_EVENT_TYPES = {MOVE_EVENT}

KEY_STARTED_AT = "started_at"
KEY_UPTIME_SECONDS = "uptime_seconds"
KEY_CONNECTION_ID = "connection_id"
KEY_CURSOR_ID = "cursor_id"
KEY_CONNECTED_AT = "connected_at"
KEY_SESSION_SECONDS = "session_seconds"
KEY_COLOR = "color"
KEY_TILE_ID = "tile_id"
KEY_X = "x"
KEY_Y = "y"
KEY_SCORE = "score"
KEY_IS_ALIVE = "is_alive"
KEY_ACTIVE_AT = "active_at"
KEY_WINDOW = "window"
KEY_WIDTH = "width"
KEY_HEIGHT = "height"
KEY_CONNECTION_COUNT = "connection_count"

ROW_ID = "id"
ROW_ADDED_AT = "added_at"
ROW_LEVEL = "level"
ROW_MODULE = "module"
ROW_FUNCTION_NAME = "function_name"
ROW_LINE = "line"
ROW_MESSAGE = "message"
ROW_CONTEXT_JSON = "context_json"
ROW_EVENT_TYPE = "event_type"
ROW_ACTOR_ID = "actor_id"
ROW_VALUE = "value"
ROW_PAYLOAD_JSON = "payload_json"
ROW_FIRST_SEEN_AT = "first_seen_at"
ROW_LAST_SEEN_AT = "last_seen_at"


@dataclass(frozen=True)
class CursorWindow:
    width: int | None = None
    height: int | None = None


@dataclass(frozen=True)
class Uptime:
    started_at: str | None = None
    uptime_seconds: int = 0


@dataclass(frozen=True)
class ActiveCursor:
    connection_id: str
    cursor_id: str
    color: int | None = None
    tile_id: str | None = None
    x: int | None = None
    y: int | None = None
    score: int = 0
    is_alive: bool = True
    active_at: str | None = None
    window: CursorWindow = field(default_factory=CursorWindow)
    connected_at: str | None = None
    session_seconds: int = 0


@dataclass
class CursorSnapshot:
    connection_id: str
    cursor_id: str
    connected_at: str | None = None
    session_seconds: int = 0
    color: int | None = None
    tile_id: str | None = None
    x: int | None = None
    y: int | None = None
    score: int = 0
    is_alive: bool = True
    active_at: str | None = None
    last_event_at: str | None = None
    is_connected: bool = False
    window: CursorWindow = field(default_factory=CursorWindow)

    def to_active_cursor(self) -> ActiveCursor:
        return ActiveCursor(
            connection_id=self.connection_id,
            cursor_id=self.cursor_id,
            color=self.color,
            tile_id=self.tile_id,
            x=self.x,
            y=self.y,
            score=self.score,
            is_alive=self.is_alive,
            active_at=self.active_at,
            window=self.window,
            connected_at=self.connected_at,
            session_seconds=self.session_seconds,
        )


@dataclass(frozen=True)
class AppLog:
    id: int
    added_at: str
    level: str
    module: str | None
    function_name: str | None
    line: int | None
    message: str
    context: JsonObject


@dataclass(frozen=True)
class StatEvent:
    id: int
    added_at: str
    event_type: str
    actor_id: str | None
    tile_id: str | None
    x: int | None
    y: int | None
    value: int | None
    payload: JsonObject


@dataclass(frozen=True)
class DashboardSummary:
    total_events: int
    joins: int
    quits: int
    current_connections: int
    active_cursors: int
    created_cursors: int
    moves: int
    opened_tiles: int
    flags: int
    explosions: int
    debug_logs: int


@dataclass(frozen=True)
class RuntimeSummary:
    current_connections: int
    active_cursors: int
    process_uptime_seconds: int
    started_at: str | None


@dataclass(frozen=True)
class StoredSummary:
    total_events: int
    first_seen_at: str | None
    last_seen_at: str | None
    observed_seconds: int


@dataclass(frozen=True)
class EventCount:
    event_type: str
    count: int


@dataclass(frozen=True)
class ActivityBucket:
    bucket_start: str
    join: int
    quit: int
    move: int
    create_cursor: int
    open_tile: int
    set_flag: int
    explosion: int


@dataclass(frozen=True)
class HourlyConnection:
    hour_start: str
    joins: int
    quits: int
    peak_connections: int
    end_connections: int


@dataclass
class PlayerStat:
    actor_id: str
    event_count: int = 0
    move_count: int = 0
    join_count: int = 0
    quit_count: int = 0
    last_event_at: str | None = None
    last_tile_id: str | None = None


@dataclass(frozen=True)
class ColorStat:
    color: str
    count: int


@dataclass
class TileStat:
    tile_id: str
    x: int | None
    y: int | None
    count: int = 0
    last_event_type: str | None = None
    last_event_at: str | None = None


async def get_dashboard(
    db: DB,
    range_value: str = DEFAULT_RANGE_VALUE,
    bucket: str = DEFAULT_BUCKET,
    limit: int = DEFAULT_LIMIT,
    active_cursors: list[Mapping[str, object]] | None = None,
    current_connections: int | None = None,
    uptime: Mapping[str, object] | None = None,
) -> JsonObject:
    now = datetime.now(timezone.utc)
    limit = max(MIN_LIMIT, min(limit, MAX_LIMIT))
    uptime_state = _uptime(uptime)

    total_stat_events = await get_total_stat_event_count(db)
    observed_range = await get_stat_event_observed_range(db)
    since_dt = _since_datetime(range_value, now, observed_range)
    since = _format_z(since_dt)
    stat_events = [_stat_event(row) for row in await get_stat_events_since(db, since)]
    if _is_all_range(range_value):
        all_stat_events = stat_events
    else:
        all_stat_events = [
            _stat_event(row)
            for row in await get_stat_events_since(db, ALL_EVENTS_SINCE)
        ]
    previous_connection_count = _previous_connection_count(
        await get_previous_connection_payloads(
            db,
            since,
            PREVIOUS_CONNECTION_LOOKBACK_LIMIT,
        )
    )
    recent_events = [_stat_event(row) for row in await get_recent_stat_events(db, limit)]
    recent_logs = [_app_log(row) for row in await get_recent_app_logs(db, limit)]
    active_cursor_list = _with_connection_times(
        await get_latest_join_times(db),
        [_active_cursor(cursor) for cursor in active_cursors or []],
        now,
    )

    event_counts = Counter(event.event_type for event in stat_events)
    if current_connections is None:
        current_connections = _current_connections(stat_events)

    summary = DashboardSummary(
        total_events=len(stat_events),
        joins=event_counts.get(JOIN_EVENT, 0),
        quits=event_counts.get(QUIT_EVENT, 0),
        current_connections=current_connections,
        active_cursors=len(active_cursor_list),
        created_cursors=event_counts.get(CREATE_CURSOR_EVENT, 0),
        moves=event_counts.get(MOVE_EVENT, 0),
        opened_tiles=event_counts.get(OPEN_TILE_EVENT, 0),
        flags=event_counts.get(SET_FLAG_EVENT, 0),
        explosions=event_counts.get(EXPLOSION_EVENT, 0),
        debug_logs=sum(1 for log in recent_logs if log.level == DEBUG_LEVEL),
    )
    runtime = RuntimeSummary(
        current_connections=current_connections,
        active_cursors=len(active_cursor_list),
        process_uptime_seconds=uptime_state.uptime_seconds,
        started_at=uptime_state.started_at,
    )
    stored = _stored_summary(
        observed_range,
        total_events=total_stat_events,
        now=now,
    )
    tile_stats = _tile_stats(stat_events)
    tile_heatmap_stats = _tile_stats(
        [
            event
            for event in stat_events
            if event.event_type in TILE_HEATMAP_EVENT_TYPES
        ]
    )

    return {
        "server_time": datetime.now(timezone.utc).isoformat(),
        "range": range_value,
        "bucket": bucket,
        "summary": asdict(summary),
        "runtime": asdict(runtime),
        "stored": asdict(stored),
        "uptime": asdict(uptime_state),
        "event_counts": _asdict_list(_event_counts(event_counts)),
        "activity": _asdict_list(_activity(stat_events, bucket)),
        "hourly_connections": _asdict_list(
            _hourly_connections(
                stat_events,
                since_dt=since_dt,
                now=now,
                initial_connections=previous_connection_count,
            )
        ),
        "players": _asdict_list(_players(stat_events)),
        "colors": _asdict_list(_colors(stat_events)),
        "tiles": _asdict_list(_tiles(tile_stats)),
        "tile_heatmap": _asdict_list(tile_heatmap_stats),
        "active_cursors": _asdict_list(active_cursor_list),
        "last_known_cursors": _asdict_list(_last_known_cursors(all_stat_events, now)),
        "recent_events": _asdict_list(recent_events),
        "recent_logs": _asdict_list(recent_logs),
    }


def _stored_summary(row, *, total_events: int, now: datetime) -> StoredSummary:
    first_seen_at = _str_or_none(row[ROW_FIRST_SEEN_AT]) if row is not None else None
    last_seen_at = _str_or_none(row[ROW_LAST_SEEN_AT]) if row is not None else None
    return StoredSummary(
        total_events=total_events,
        first_seen_at=first_seen_at,
        last_seen_at=last_seen_at,
        observed_seconds=_observed_seconds(first_seen_at, now),
    )


def _observed_seconds(first_seen_at: str | None, now: datetime) -> int:
    if first_seen_at is None:
        return 0
    return max(
        0,
        int((now - _parse_added_at(first_seen_at).astimezone(timezone.utc)).total_seconds()),
    )


def _previous_connection_count(rows) -> int:
    for row in rows:
        connection_count = _json(row[ROW_PAYLOAD_JSON]).get(KEY_CONNECTION_COUNT)
        if isinstance(connection_count, int):
            return connection_count
    return 0


def _with_connection_times(
    join_rows,
    active_cursors: list[ActiveCursor],
    now: datetime,
) -> list[ActiveCursor]:
    if not active_cursors:
        return []

    actor_ids = [
        cursor.cursor_id
        for cursor in active_cursors
        if cursor.cursor_id
    ]
    if not actor_ids:
        return [
            replace(cursor, connected_at=None, session_seconds=0)
            for cursor in active_cursors
        ]

    actor_id_set = set(actor_ids)
    connected_at_by_actor: dict[str, str | None] = {}
    for row in join_rows:
        actor_id = _str_or_none(row[ROW_ACTOR_ID])
        if actor_id in actor_id_set:
            connected_at_by_actor[actor_id] = _str_or_none(row[KEY_CONNECTED_AT])

    return [
        replace(
            cursor,
            connected_at=connected_at_by_actor.get(cursor.cursor_id),
            session_seconds=_session_seconds(connected_at_by_actor.get(cursor.cursor_id), now),
        )
        for cursor in active_cursors
    ]


def _app_log(row) -> AppLog:
    return AppLog(
        id=_int_or_default(row[ROW_ID]),
        added_at=_str_or_empty(row[ROW_ADDED_AT]),
        level=_str_or_empty(row[ROW_LEVEL]),
        module=_str_or_none(row[ROW_MODULE]),
        function_name=_str_or_none(row[ROW_FUNCTION_NAME]),
        line=_int_or_none(row[ROW_LINE]),
        message=_str_or_empty(row[ROW_MESSAGE]),
        context=_json(row[ROW_CONTEXT_JSON]),
    )


def _stat_event(row) -> StatEvent:
    return StatEvent(
        id=_int_or_default(row[ROW_ID]),
        added_at=_str_or_empty(row[ROW_ADDED_AT]),
        event_type=_str_or_empty(row[ROW_EVENT_TYPE]),
        actor_id=_str_or_none(row[ROW_ACTOR_ID]),
        tile_id=_str_or_none(row[KEY_TILE_ID]),
        x=_int_or_none(row[KEY_X]),
        y=_int_or_none(row[KEY_Y]),
        value=_int_or_none(row[ROW_VALUE]),
        payload=_json(row[ROW_PAYLOAD_JSON]),
    )


def _json(value: str | None) -> JsonObject:
    if not value:
        return {}
    try:
        decoded = json.loads(value)
    except json.JSONDecodeError:
        return {}
    if not isinstance(decoded, Mapping):
        return {}
    return {str(key): _json_value(val) for key, val in decoded.items()}


def _json_value(value: object | None) -> JsonValue:
    if value is None or isinstance(value, bool | int | float | str):
        return value
    if isinstance(value, Mapping):
        return {str(key): _json_value(val) for key, val in value.items()}
    if isinstance(value, Sequence) and not isinstance(value, str | bytes | bytearray):
        return [_json_value(item) for item in value]
    return str(value)


def _since_datetime(range_value: str, now: datetime, observed_range=None) -> datetime:
    if _is_all_range(range_value):
        first_seen_at = _str_or_none(observed_range[ROW_FIRST_SEEN_AT]) if observed_range is not None else None
        if first_seen_at is not None:
            return _parse_added_at(first_seen_at).astimezone(timezone.utc)
        return now

    amount = int(range_value[:-1]) if range_value[:-1].isdigit() else DEFAULT_RANGE_AMOUNT
    unit = range_value[-1:] if range_value else HOURS_UNIT
    if unit == MINUTES_UNIT:
        delta = timedelta(minutes=amount)
    elif unit == DAYS_UNIT:
        delta = timedelta(days=amount)
    else:
        delta = timedelta(hours=amount)
    return now - delta


def _is_all_range(range_value: str) -> bool:
    return range_value.lower() == ALL_RANGE_VALUE


def _format_z(value: datetime) -> str:
    return value.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")


def _event_counts(counter: Counter[str]) -> list[EventCount]:
    return [
        EventCount(event_type=event_type, count=count)
        for event_type, count in counter.most_common()
    ]


def _current_connections(events: list[StatEvent]) -> int:
    for event in reversed(events):
        if event.event_type not in {JOIN_EVENT, QUIT_EVENT}:
            continue
        connection_count = event.payload.get(KEY_CONNECTION_COUNT)
        if isinstance(connection_count, int):
            return connection_count
    return 0


def _last_known_cursors(events: list[StatEvent], now: datetime) -> list[ActiveCursor]:
    cursors: dict[str, CursorSnapshot] = {}
    for event in events:
        actor_id = event.actor_id
        if actor_id is None:
            continue

        cursor = cursors.setdefault(
            actor_id,
            CursorSnapshot(
                connection_id=actor_id,
                cursor_id=actor_id,
            ),
        )
        _apply_last_known_event(cursor, event)

    result: list[ActiveCursor] = []
    for cursor in cursors.values():
        if not cursor.is_connected:
            continue
        cursor.session_seconds = _session_seconds(cursor.connected_at, now)
        result.append(cursor.to_active_cursor())

    return sorted(
        result,
        key=lambda cursor: cursor.active_at or "",
        reverse=True,
    )


def _apply_last_known_event(cursor: CursorSnapshot, event: StatEvent) -> None:
    cursor.last_event_at = event.added_at
    cursor.active_at = event.added_at

    if event.event_type == JOIN_EVENT:
        cursor.connected_at = event.added_at
        cursor.is_connected = True
    elif event.event_type == QUIT_EVENT:
        cursor.is_connected = False

    if event.event_type == CREATE_CURSOR_EVENT:
        cursor.color = _int_or_none(event.payload.get(KEY_COLOR))
        cursor.window = CursorWindow(
            width=_int_or_none(event.payload.get(KEY_WIDTH)),
            height=_int_or_none(event.payload.get(KEY_HEIGHT)),
        )

    if event.tile_id is not None:
        cursor.tile_id = event.tile_id
    if event.x is not None:
        cursor.x = event.x
    if event.y is not None:
        cursor.y = event.y

    if event.event_type == SCORE_CHANGE_EVENT and event.value is not None:
        cursor.score += event.value


def _activity(events: list[StatEvent], bucket: str) -> list[ActivityBucket]:
    buckets = defaultdict(Counter)
    for event in events:
        key = _bucket_start(event.added_at, bucket)
        buckets[key][event.event_type] += 1

    return [
        ActivityBucket(
            bucket_start=key,
            join=counter.get(JOIN_EVENT, 0),
            quit=counter.get(QUIT_EVENT, 0),
            move=counter.get(MOVE_EVENT, 0),
            create_cursor=counter.get(CREATE_CURSOR_EVENT, 0),
            open_tile=counter.get(OPEN_TILE_EVENT, 0),
            set_flag=counter.get(SET_FLAG_EVENT, 0),
            explosion=counter.get(EXPLOSION_EVENT, 0),
        )
        for key, counter in sorted(buckets.items())
    ]


def _hourly_connections(
    events: list[StatEvent],
    *,
    since_dt: datetime,
    now: datetime,
    initial_connections: int,
) -> list[HourlyConnection]:
    hour = since_dt.replace(minute=0, second=0, microsecond=0)
    end_hour = now.replace(minute=0, second=0, microsecond=0)
    event_index = 0
    connection_events = [
        event
        for event in events
        if event.event_type in {JOIN_EVENT, QUIT_EVENT}
    ]
    current_connections = initial_connections
    result: list[HourlyConnection] = []

    while hour <= end_hour:
        next_hour = hour + timedelta(hours=1)
        joins = 0
        quits = 0
        peak_connections = current_connections

        while event_index < len(connection_events):
            event = connection_events[event_index]
            event_dt = _parse_added_at(event.added_at).astimezone(timezone.utc)
            if event_dt >= next_hour:
                break

            event_index += 1
            if event_dt < since_dt:
                continue

            if event.event_type == JOIN_EVENT:
                joins += 1
            elif event.event_type == QUIT_EVENT:
                quits += 1

            connection_count = event.payload.get(KEY_CONNECTION_COUNT)
            if isinstance(connection_count, int):
                current_connections = connection_count
                peak_connections = max(peak_connections, current_connections)

        result.append(
            HourlyConnection(
                hour_start=_format_z(hour),
                joins=joins,
                quits=quits,
                peak_connections=peak_connections,
                end_connections=current_connections,
            )
        )
        hour = next_hour

    return result


def _bucket_start(value: str, bucket: str) -> str:
    dt = _parse_added_at(value)
    if bucket == HOUR_BUCKET:
        dt = dt.replace(minute=0, second=0, microsecond=0)
    elif bucket == FIVE_MINUTE_BUCKET:
        minute = dt.minute - (dt.minute % FIVE_MINUTE_BUCKET_SIZE)
        dt = dt.replace(minute=minute, second=0, microsecond=0)
    else:
        dt = dt.replace(second=0, microsecond=0)
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def _parse_added_at(value: str) -> datetime:
    normalized = value.replace("Z", "+00:00")
    return datetime.fromisoformat(normalized)


def _session_seconds(connected_at: str | None, now: datetime) -> int:
    if connected_at is None:
        return 0
    return max(
        0,
        int((now - _parse_added_at(connected_at).astimezone(timezone.utc)).total_seconds()),
    )


def _players(events: list[StatEvent]) -> list[PlayerStat]:
    players: dict[str, PlayerStat] = {}
    for event in events:
        actor_id = event.actor_id
        if actor_id is None:
            continue
        player = players.setdefault(actor_id, PlayerStat(actor_id=actor_id))
        player.event_count += 1
        player.move_count += 1 if event.event_type == MOVE_EVENT else 0
        player.join_count += 1 if event.event_type == JOIN_EVENT else 0
        player.quit_count += 1 if event.event_type == QUIT_EVENT else 0
        player.last_event_at = event.added_at
        if event.tile_id is not None:
            player.last_tile_id = event.tile_id

    return sorted(
        players.values(),
        key=lambda player: player.event_count,
        reverse=True,
    )[:TOP_PLAYERS_LIMIT]


def _colors(events: list[StatEvent]) -> list[ColorStat]:
    counter: Counter[str] = Counter()
    for event in events:
        if event.event_type != CREATE_CURSOR_EVENT:
            continue
        color = event.payload.get(KEY_COLOR)
        if color is not None:
            counter[str(color)] += 1

    return [
        ColorStat(color=color, count=count)
        for color, count in counter.most_common()
    ]


def _tiles(tile_stats: list[TileStat]) -> list[TileStat]:
    return tile_stats[:TOP_TILES_LIMIT]


def _tile_stats(events: list[StatEvent]) -> list[TileStat]:
    tiles: dict[str, TileStat] = {}
    for event in events:
        tile_id = event.tile_id
        if tile_id is None:
            continue
        tile = tiles.setdefault(
            tile_id,
            TileStat(
                tile_id=tile_id,
                x=event.x,
                y=event.y,
            ),
        )
        tile.count += 1
        tile.last_event_type = event.event_type
        tile.last_event_at = event.added_at

    return sorted(
        tiles.values(),
        key=lambda tile: tile.count,
        reverse=True,
    )


def _active_cursor(raw: Mapping[str, object]) -> ActiveCursor:
    cursor_id = _str_or_empty(raw.get(KEY_CURSOR_ID))
    return ActiveCursor(
        connection_id=_str_or_default(raw.get(KEY_CONNECTION_ID), cursor_id),
        cursor_id=cursor_id,
        color=_int_or_none(raw.get(KEY_COLOR)),
        tile_id=_str_or_none(raw.get(KEY_TILE_ID)),
        x=_int_or_none(raw.get(KEY_X)),
        y=_int_or_none(raw.get(KEY_Y)),
        score=_int_or_default(raw.get(KEY_SCORE)),
        is_alive=_bool_or_default(raw.get(KEY_IS_ALIVE), True),
        active_at=_str_or_none(raw.get(KEY_ACTIVE_AT)),
        window=_window(raw.get(KEY_WINDOW)),
    )


def _window(raw: object | None) -> CursorWindow:
    if not isinstance(raw, Mapping):
        return CursorWindow()
    return CursorWindow(
        width=_int_or_none(raw.get(KEY_WIDTH)),
        height=_int_or_none(raw.get(KEY_HEIGHT)),
    )


def _uptime(raw: Mapping[str, object] | None) -> Uptime:
    if raw is None:
        return Uptime()
    return Uptime(
        started_at=_str_or_none(raw.get(KEY_STARTED_AT)),
        uptime_seconds=_int_or_default(raw.get(KEY_UPTIME_SECONDS)),
    )


def _asdict_list(items) -> list[JsonObject]:
    return [asdict(item) for item in items]


def _str_or_none(value: object | None) -> str | None:
    if value is None:
        return None
    return str(value)


def _str_or_empty(value: object | None) -> str:
    if value is None:
        return ""
    return str(value)


def _str_or_default(value: object | None, default: str) -> str:
    if value is None:
        return default
    return str(value)


def _int_or_none(value: object | None) -> int | None:
    if isinstance(value, int):
        return value
    return None


def _int_or_default(value: object | None, default: int = 0) -> int:
    if isinstance(value, int):
        return value
    return default


def _bool_or_default(value: object | None, default: bool) -> bool:
    if isinstance(value, bool):
        return value
    return default
