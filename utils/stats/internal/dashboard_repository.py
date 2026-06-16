from __future__ import annotations

from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
import json
from typing import Any

from handler.board.storage import get_db
from utils.logging import (
    get_latest_join_times,
    get_previous_connection_payloads,
    get_recent_app_logs,
    get_recent_stat_events,
    get_stat_event_observed_range,
    get_stat_events_since,
    get_total_stat_event_count,
)

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


async def get_dashboard(
    range_value: str = DEFAULT_RANGE_VALUE,
    bucket: str = DEFAULT_BUCKET,
    limit: int = DEFAULT_LIMIT,
    active_cursors: list[dict[str, Any]] | None = None,
    current_connections: int | None = None,
    uptime: dict[str, Any] | None = None,
):
    now = datetime.now(timezone.utc)
    limit = max(MIN_LIMIT, min(limit, MAX_LIMIT))

    async with get_db() as db:
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
        active_cursors = _with_connection_times(
            await get_latest_join_times(db),
            active_cursors or [],
            now,
        )

    event_counts = Counter(event["event_type"] for event in stat_events)
    if current_connections is None:
        current_connections = _current_connections(stat_events)

    summary = {
        "total_events": len(stat_events),
        "joins": event_counts.get(JOIN_EVENT, 0),
        "quits": event_counts.get(QUIT_EVENT, 0),
        "current_connections": current_connections,
        "active_cursors": len(active_cursors),
        "created_cursors": event_counts.get(CREATE_CURSOR_EVENT, 0),
        "moves": event_counts.get(MOVE_EVENT, 0),
        "opened_tiles": event_counts.get(OPEN_TILE_EVENT, 0),
        "flags": event_counts.get(SET_FLAG_EVENT, 0),
        "explosions": event_counts.get(EXPLOSION_EVENT, 0),
        "debug_logs": sum(1 for log in recent_logs if log["level"] == DEBUG_LEVEL),
    }
    runtime = {
        "current_connections": current_connections,
        "active_cursors": len(active_cursors),
        "process_uptime_seconds": (uptime or {}).get("uptime_seconds", 0),
        "started_at": (uptime or {}).get("started_at"),
    }
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
            if event["event_type"] in TILE_HEATMAP_EVENT_TYPES
        ]
    )

    return {
        "server_time": datetime.now(timezone.utc).isoformat(),
        "range": range_value,
        "bucket": bucket,
        "summary": summary,
        "runtime": runtime,
        "stored": stored,
        "uptime": uptime or {},
        "event_counts": _event_counts(event_counts),
        "activity": _activity(stat_events, bucket),
        "hourly_connections": _hourly_connections(
            stat_events,
            since_dt=since_dt,
            now=now,
            initial_connections=previous_connection_count,
        ),
        "players": _players(stat_events),
        "colors": _colors(stat_events),
        "tiles": _tiles(tile_stats),
        "tile_heatmap": tile_heatmap_stats,
        "active_cursors": active_cursors,
        "last_known_cursors": _last_known_cursors(all_stat_events, now),
        "recent_events": recent_events,
        "recent_logs": recent_logs,
    }


def _stored_summary(row, *, total_events: int, now: datetime):
    first_seen_at = row["first_seen_at"] if row is not None else None
    last_seen_at = row["last_seen_at"] if row is not None else None
    return {
        "total_events": total_events,
        "first_seen_at": first_seen_at,
        "last_seen_at": last_seen_at,
        "observed_seconds": _observed_seconds(first_seen_at, now),
    }


def _observed_seconds(first_seen_at: str | None, now: datetime):
    if first_seen_at is None:
        return 0
    return max(
        0,
        int((now - _parse_added_at(first_seen_at).astimezone(timezone.utc)).total_seconds()),
    )


def _previous_connection_count(rows):
    for row in rows:
        connection_count = _json(row["payload_json"]).get("connection_count")
        if isinstance(connection_count, int):
            return connection_count
    return 0


def _with_connection_times(
    join_rows,
    active_cursors: list[dict[str, Any]],
    now: datetime,
):
    if not active_cursors:
        return []

    actor_ids = [
        cursor["cursor_id"]
        for cursor in active_cursors
        if cursor.get("cursor_id") is not None
    ]
    if not actor_ids:
        return [
            {
                **cursor,
                "connected_at": None,
                "session_seconds": 0,
            }
            for cursor in active_cursors
        ]

    actor_id_set = set(actor_ids)
    connected_at_by_actor = {
        row["actor_id"]: row["connected_at"]
        for row in join_rows
        if row["actor_id"] in actor_id_set
    }

    result = []
    for cursor in active_cursors:
        connected_at = connected_at_by_actor.get(cursor.get("cursor_id"))
        result.append(
            {
                **cursor,
                "connected_at": connected_at,
                "session_seconds": _session_seconds(connected_at, now),
            }
        )
    return result


def _app_log(row):
    return {
        "id": row["id"],
        "added_at": row["added_at"],
        "level": row["level"],
        "module": row["module"],
        "function_name": row["function_name"],
        "line": row["line"],
        "message": row["message"],
        "context": _json(row["context_json"]),
    }


def _stat_event(row):
    return {
        "id": row["id"],
        "added_at": row["added_at"],
        "event_type": row["event_type"],
        "actor_id": row["actor_id"],
        "tile_id": row["tile_id"],
        "x": row["x"],
        "y": row["y"],
        "value": row["value"],
        "payload": _json(row["payload_json"]),
    }


def _json(value: str | None):
    if not value:
        return {}
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return {}


def _since_datetime(range_value: str, now: datetime, observed_range=None):
    if _is_all_range(range_value):
        first_seen_at = observed_range["first_seen_at"] if observed_range is not None else None
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


def _is_all_range(range_value: str):
    return range_value.lower() == ALL_RANGE_VALUE


def _format_z(value: datetime):
    return value.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")


def _event_counts(counter: Counter[str]):
    return [
        {"event_type": event_type, "count": count}
        for event_type, count in counter.most_common()
    ]


def _current_connections(events: list[dict[str, Any]]):
    for event in reversed(events):
        if event["event_type"] not in {JOIN_EVENT, QUIT_EVENT}:
            continue
        connection_count = event["payload"].get("connection_count")
        if isinstance(connection_count, int):
            return connection_count
    return 0


def _last_known_cursors(events: list[dict[str, Any]], now: datetime):
    cursors: dict[str, dict[str, Any]] = {}
    for event in events:
        actor_id = event["actor_id"]
        if actor_id is None:
            continue

        cursor = cursors.setdefault(
            actor_id,
            {
                "connection_id": actor_id,
                "cursor_id": actor_id,
                "connected_at": None,
                "session_seconds": 0,
                "color": None,
                "tile_id": None,
                "x": None,
                "y": None,
                "score": 0,
                "is_alive": True,
                "active_at": None,
                "last_event_at": None,
                "is_connected": False,
                "window": {
                    "width": None,
                    "height": None,
                },
            },
        )
        _apply_last_known_event(cursor, event)

    result = []
    for cursor in cursors.values():
        if not cursor["is_connected"]:
            continue
        cursor["session_seconds"] = _session_seconds(cursor["connected_at"], now)
        result.append(cursor)

    return sorted(
        result,
        key=lambda cursor: cursor["last_event_at"] or "",
        reverse=True,
    )


def _apply_last_known_event(cursor: dict[str, Any], event: dict[str, Any]):
    event_type = event["event_type"]
    cursor["last_event_at"] = event["added_at"]
    cursor["active_at"] = event["added_at"]

    if event_type == JOIN_EVENT:
        cursor["connected_at"] = event["added_at"]
        cursor["is_connected"] = True
    elif event_type == QUIT_EVENT:
        cursor["is_connected"] = False

    if event_type == CREATE_CURSOR_EVENT:
        cursor["color"] = event["payload"].get("color")
        cursor["window"] = {
            "width": event["payload"].get("width"),
            "height": event["payload"].get("height"),
        }

    if event["tile_id"] is not None:
        cursor["tile_id"] = event["tile_id"]
    if event["x"] is not None:
        cursor["x"] = event["x"]
    if event["y"] is not None:
        cursor["y"] = event["y"]

    if event_type == SCORE_CHANGE_EVENT and isinstance(event["value"], int):
        cursor["score"] += event["value"]


def _activity(events: list[dict[str, Any]], bucket: str):
    buckets: dict[str, Counter[str]] = defaultdict(Counter)
    for event in events:
        key = _bucket_start(event["added_at"], bucket)
        buckets[key][event["event_type"]] += 1

    return [
        {
            "bucket_start": key,
            "join": counter.get(JOIN_EVENT, 0),
            "quit": counter.get(QUIT_EVENT, 0),
            "move": counter.get(MOVE_EVENT, 0),
            "create_cursor": counter.get(CREATE_CURSOR_EVENT, 0),
            "open_tile": counter.get(OPEN_TILE_EVENT, 0),
            "set_flag": counter.get(SET_FLAG_EVENT, 0),
            "explosion": counter.get(EXPLOSION_EVENT, 0),
        }
        for key, counter in sorted(buckets.items())
    ]


def _hourly_connections(
    events: list[dict[str, Any]],
    *,
    since_dt: datetime,
    now: datetime,
    initial_connections: int,
):
    hour = since_dt.replace(minute=0, second=0, microsecond=0)
    end_hour = now.replace(minute=0, second=0, microsecond=0)
    event_index = 0
    connection_events = [
        event
        for event in events
        if event["event_type"] in {JOIN_EVENT, QUIT_EVENT}
    ]
    current_connections = initial_connections
    result = []

    while hour <= end_hour:
        next_hour = hour + timedelta(hours=1)
        joins = 0
        quits = 0
        peak_connections = current_connections

        while event_index < len(connection_events):
            event = connection_events[event_index]
            event_dt = _parse_added_at(event["added_at"]).astimezone(timezone.utc)
            if event_dt >= next_hour:
                break

            event_index += 1
            if event_dt < since_dt:
                continue

            if event["event_type"] == JOIN_EVENT:
                joins += 1
            elif event["event_type"] == QUIT_EVENT:
                quits += 1

            connection_count = event["payload"].get("connection_count")
            if isinstance(connection_count, int):
                current_connections = connection_count
                peak_connections = max(peak_connections, current_connections)

        result.append(
            {
                "hour_start": _format_z(hour),
                "joins": joins,
                "quits": quits,
                "peak_connections": peak_connections,
                "end_connections": current_connections,
            }
        )
        hour = next_hour

    return result


def _bucket_start(value: str, bucket: str):
    dt = _parse_added_at(value)
    if bucket == HOUR_BUCKET:
        dt = dt.replace(minute=0, second=0, microsecond=0)
    elif bucket == FIVE_MINUTE_BUCKET:
        minute = dt.minute - (dt.minute % FIVE_MINUTE_BUCKET_SIZE)
        dt = dt.replace(minute=minute, second=0, microsecond=0)
    else:
        dt = dt.replace(second=0, microsecond=0)
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def _parse_added_at(value: str):
    normalized = value.replace("Z", "+00:00")
    return datetime.fromisoformat(normalized)


def _session_seconds(connected_at: str | None, now: datetime):
    if connected_at is None:
        return 0
    return max(
        0,
        int((now - _parse_added_at(connected_at).astimezone(timezone.utc)).total_seconds()),
    )


def _players(events: list[dict[str, Any]]):
    players: dict[str, dict[str, Any]] = {}
    for event in events:
        actor_id = event["actor_id"]
        if actor_id is None:
            continue
        player = players.setdefault(
            actor_id,
            {
                "actor_id": actor_id,
                "event_count": 0,
                "move_count": 0,
                "join_count": 0,
                "quit_count": 0,
                "last_event_at": None,
                "last_tile_id": None,
            },
        )
        player["event_count"] += 1
        player["move_count"] += 1 if event["event_type"] == MOVE_EVENT else 0
        player["join_count"] += 1 if event["event_type"] == JOIN_EVENT else 0
        player["quit_count"] += 1 if event["event_type"] == QUIT_EVENT else 0
        player["last_event_at"] = event["added_at"]
        if event["tile_id"] is not None:
            player["last_tile_id"] = event["tile_id"]

    return sorted(
        players.values(),
        key=lambda player: player["event_count"],
        reverse=True,
    )[:TOP_PLAYERS_LIMIT]


def _colors(events: list[dict[str, Any]]):
    counter: Counter[str] = Counter()
    for event in events:
        if event["event_type"] != CREATE_CURSOR_EVENT:
            continue
        color = event["payload"].get("color")
        if color is not None:
            counter[str(color)] += 1

    return [
        {"color": color, "count": count}
        for color, count in counter.most_common()
    ]


def _tiles(tile_stats: list[dict[str, Any]]):
    return tile_stats[:TOP_TILES_LIMIT]


def _tile_stats(events: list[dict[str, Any]]):
    tiles: dict[str, dict[str, Any]] = {}
    for event in events:
        tile_id = event["tile_id"]
        if tile_id is None:
            continue
        tile = tiles.setdefault(
            tile_id,
            {
                "tile_id": tile_id,
                "x": event["x"],
                "y": event["y"],
                "count": 0,
                "last_event_type": None,
                "last_event_at": None,
            },
        )
        tile["count"] += 1
        tile["last_event_type"] = event["event_type"]
        tile["last_event_at"] = event["added_at"]

    return sorted(
        tiles.values(),
        key=lambda tile: tile["count"],
        reverse=True,
    )
