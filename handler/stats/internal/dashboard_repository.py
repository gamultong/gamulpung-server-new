from __future__ import annotations

from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
import json
import sqlite3
from typing import Any


def get_dashboard(
    db_path: str,
    *,
    range_value: str = "24h",
    bucket: str = "1m",
    limit: int = 50,
    active_cursors: list[dict[str, Any]] | None = None,
    current_connections: int | None = None,
    uptime: dict[str, Any] | None = None,
):
    now = datetime.now(timezone.utc)
    since_dt = _since_datetime(range_value, now)
    since = _format_z(since_dt)
    limit = max(1, min(limit, 200))

    with sqlite3.connect(db_path) as db:
        db.row_factory = sqlite3.Row
        stat_events = _fetch_stat_events(db, since)
        previous_connection_count = _fetch_previous_connection_count(db, since)
        recent_events = _fetch_recent_events(db, limit)
        recent_logs = _fetch_recent_logs(db, limit)

    event_counts = Counter(event["event_type"] for event in stat_events)
    active_cursors = active_cursors or []
    if current_connections is None:
        current_connections = _current_connections(stat_events)

    summary = {
        "total_events": len(stat_events),
        "joins": event_counts.get("JOIN", 0),
        "quits": event_counts.get("QUIT", 0),
        "current_connections": current_connections,
        "active_cursors": len(active_cursors),
        "created_cursors": event_counts.get("CREATE_CURSOR", 0),
        "moves": event_counts.get("MOVE", 0),
        "opened_tiles": event_counts.get("OPEN_TILE", 0),
        "flags": event_counts.get("SET_FLAG", 0),
        "explosions": event_counts.get("EXPLOSION", 0),
        "debug_logs": sum(1 for log in recent_logs if log["level"] == "DEBUG"),
    }

    return {
        "server_time": datetime.now(timezone.utc).isoformat(),
        "range": range_value,
        "bucket": bucket,
        "summary": summary,
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
        "tiles": _tiles(stat_events),
        "active_cursors": active_cursors,
        "recent_events": recent_events,
        "recent_logs": recent_logs,
    }


def _fetch_stat_events(db: sqlite3.Connection, since: str):
    if not _table_exists(db, "stat_event"):
        return []

    rows = db.execute(
        """
        SELECT id, added_at, event_type, actor_id, tile_id, x, y, value, payload_json
        FROM stat_event
        WHERE added_at >= ?
        ORDER BY id ASC
        """,
        (since,),
    ).fetchall()
    return [_stat_event(row) for row in rows]


def _fetch_previous_connection_count(db: sqlite3.Connection, since: str):
    if not _table_exists(db, "stat_event"):
        return 0

    rows = db.execute(
        """
        SELECT payload_json
        FROM stat_event
        WHERE added_at < ?
          AND event_type IN ('JOIN', 'QUIT')
        ORDER BY id DESC
        LIMIT 20
        """,
        (since,),
    ).fetchall()

    for row in rows:
        connection_count = _json(row["payload_json"]).get("connection_count")
        if isinstance(connection_count, int):
            return connection_count
    return 0


def _fetch_recent_events(db: sqlite3.Connection, limit: int):
    if not _table_exists(db, "stat_event"):
        return []

    rows = db.execute(
        """
        SELECT id, added_at, event_type, actor_id, tile_id, x, y, value, payload_json
        FROM stat_event
        ORDER BY id DESC
        LIMIT ?
        """,
        (limit,),
    ).fetchall()
    return [_stat_event(row) for row in rows]


def _fetch_recent_logs(db: sqlite3.Connection, limit: int):
    if not _table_exists(db, "app_log"):
        return []

    rows = db.execute(
        """
        SELECT id, added_at, level, module, function_name, line, message, context_json
        FROM app_log
        ORDER BY id DESC
        LIMIT ?
        """,
        (limit,),
    ).fetchall()
    return [
        {
            "id": row["id"],
            "added_at": row["added_at"],
            "level": row["level"],
            "module": row["module"],
            "function_name": row["function_name"],
            "line": row["line"],
            "message": row["message"],
            "context": _json(row["context_json"]),
        }
        for row in rows
    ]


def _table_exists(db: sqlite3.Connection, table_name: str):
    row = db.execute(
        "SELECT name FROM sqlite_master WHERE type = 'table' AND name = ?",
        (table_name,),
    ).fetchone()
    return row is not None


def _stat_event(row: sqlite3.Row):
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


def _since_datetime(range_value: str, now: datetime):
    amount = int(range_value[:-1]) if range_value[:-1].isdigit() else 24
    unit = range_value[-1:] if range_value else "h"
    if unit == "m":
        delta = timedelta(minutes=amount)
    elif unit == "d":
        delta = timedelta(days=amount)
    else:
        delta = timedelta(hours=amount)
    return now - delta


def _format_z(value: datetime):
    return value.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")


def _event_counts(counter: Counter[str]):
    return [
        {"event_type": event_type, "count": count}
        for event_type, count in counter.most_common()
    ]


def _current_connections(events: list[dict[str, Any]]):
    for event in reversed(events):
        if event["event_type"] not in {"JOIN", "QUIT"}:
            continue
        connection_count = event["payload"].get("connection_count")
        if isinstance(connection_count, int):
            return connection_count
    return 0


def _activity(events: list[dict[str, Any]], bucket: str):
    buckets: dict[str, Counter[str]] = defaultdict(Counter)
    for event in events:
        key = _bucket_start(event["added_at"], bucket)
        buckets[key][event["event_type"]] += 1

    return [
        {
            "bucket_start": key,
            "join": counter.get("JOIN", 0),
            "quit": counter.get("QUIT", 0),
            "move": counter.get("MOVE", 0),
            "create_cursor": counter.get("CREATE_CURSOR", 0),
            "open_tile": counter.get("OPEN_TILE", 0),
            "set_flag": counter.get("SET_FLAG", 0),
            "explosion": counter.get("EXPLOSION", 0),
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
        if event["event_type"] in {"JOIN", "QUIT"}
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

            if event["event_type"] == "JOIN":
                joins += 1
            elif event["event_type"] == "QUIT":
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
    if bucket == "1h":
        dt = dt.replace(minute=0, second=0, microsecond=0)
    elif bucket == "5m":
        minute = dt.minute - (dt.minute % 5)
        dt = dt.replace(minute=minute, second=0, microsecond=0)
    else:
        dt = dt.replace(second=0, microsecond=0)
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def _parse_added_at(value: str):
    normalized = value.replace("Z", "+00:00")
    return datetime.fromisoformat(normalized)


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
        player["move_count"] += 1 if event["event_type"] == "MOVE" else 0
        player["join_count"] += 1 if event["event_type"] == "JOIN" else 0
        player["quit_count"] += 1 if event["event_type"] == "QUIT" else 0
        player["last_event_at"] = event["added_at"]
        if event["tile_id"] is not None:
            player["last_tile_id"] = event["tile_id"]

    return sorted(players.values(), key=lambda player: player["event_count"], reverse=True)[:20]


def _colors(events: list[dict[str, Any]]):
    counter: Counter[str] = Counter()
    for event in events:
        if event["event_type"] != "CREATE_CURSOR":
            continue
        color = event["payload"].get("color")
        if color is not None:
            counter[str(color)] += 1

    return [
        {"color": color, "count": count}
        for color, count in counter.most_common()
    ]


def _tiles(events: list[dict[str, Any]]):
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

    return sorted(tiles.values(), key=lambda tile: tile["count"], reverse=True)[:20]
