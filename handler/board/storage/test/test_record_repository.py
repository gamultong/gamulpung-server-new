import os
import tempfile
from unittest.mock import patch

import aiosqlite
import pytest
import pytest_asyncio
from loguru import logger

from config import BoardConfig
from data.board import Point
from handler.board.storage import (
    _get_db,
    insert_stat_event,
    set_app_log_table,
    set_stat_event_table,
)
from utils.stats import record_stat_event
from utils.logging import AppLogDbSink


@pytest_asyncio.fixture()
async def record_db():
    db_fd, db_path = tempfile.mkstemp(suffix=".db")
    db_patch = patch.object(BoardConfig, "DB_PATH", new=db_path)
    db_patch.start()

    async with _get_db() as db:
        await set_app_log_table(db)
        await set_stat_event_table(db)

    try:
        yield db_path
    finally:
        db_patch.stop()
        os.close(db_fd)
        os.remove(db_path)


@pytest.mark.asyncio
async def test_record_tables_create_app_log_and_stat_event(record_db):
    async with aiosqlite.connect(record_db) as db:
        async with db.execute(
            """
            SELECT name
            FROM sqlite_master
            WHERE type = 'table' AND name IN ('app_log', 'stat_event')
            ORDER BY name
            """
        ) as cur:
            rows = await cur.fetchall()

    assert [row[0] for row in rows] == ["app_log", "stat_event"]


@pytest.mark.asyncio
async def test_db_log_sink_writes_loguru_logs_to_app_log(record_db):
    sink_id = logger.add(AppLogDbSink(record_db), level="INFO")
    try:
        logger.bind(test_name="db_logging").info("db log smoke")
    finally:
        logger.remove(sink_id)

    async with aiosqlite.connect(record_db) as db:
        async with db.execute(
            """
            SELECT level, message, context_json
            FROM app_log
            WHERE message = ?
            """,
            ("db log smoke",),
        ) as cur:
            row = await cur.fetchone()

    assert row[0] == "INFO"
    assert row[1] == "db log smoke"
    assert '"test_name": "db_logging"' in row[2]


@pytest.mark.asyncio
async def test_insert_stat_event_records_json_payload(record_db):
    async with _get_db() as db:
        await insert_stat_event(
            db,
            event_type="OPEN_TILE",
            actor_id="player-1",
            tile_id="tile:3:-2",
            x=3,
            y=-2,
            value=1,
            payload={"score_delta": 100},
        )

    async with aiosqlite.connect(record_db) as db:
        async with db.execute(
            """
            SELECT event_type, actor_id, tile_id, x, y, value, payload_json
            FROM stat_event
            WHERE event_type = ?
            """,
            ("OPEN_TILE",),
        ) as cur:
            row = await cur.fetchone()

    assert row[0] == "OPEN_TILE"
    assert row[1] == "player-1"
    assert row[2] == "tile:3:-2"
    assert row[3] == 3
    assert row[4] == -2
    assert row[5] == 1
    assert '"score_delta": 100' in row[6]


@pytest.mark.asyncio
async def test_record_stat_event_records_tile_event(record_db):
    await record_stat_event(
        "MOVE",
        actor_id="player-1",
        point=Point(4, 5),
        value=1,
        payload={"source": "test"},
    )

    async with aiosqlite.connect(record_db) as db:
        async with db.execute(
            """
            SELECT event_type, actor_id, tile_id, x, y, value, payload_json
            FROM stat_event
            WHERE event_type = ?
            """,
            ("MOVE",),
        ) as cur:
            row = await cur.fetchone()

    assert row[0] == "MOVE"
    assert row[1] == "player-1"
    assert row[2] == "tile:4:5"
    assert row[3] == 4
    assert row[4] == 5
    assert row[5] == 1
    assert '"source": "test"' in row[6]
