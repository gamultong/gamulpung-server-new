import os
import tempfile
from unittest import IsolatedAsyncioTestCase
from unittest.mock import patch

from loguru import logger

from config import BoardConfig
from core.lifecycle import HLife, Parameter
from data.board import Point
from data.cursor import Cursor, Items, ItemType
from data.cursor_board import Color
from handler.board.storage import (
    get_db,
    get_app_log_by_message,
    get_record_table_names,
    get_stat_event_observed_range,
    get_stat_event_by_type,
    get_total_stat_event_count,
    insert_stat_event,
    set_app_log_table,
    set_stat_event_table,
)
from utils.logging import AppLogDbSink
from utils.stats import get_dashboard, record_lifecycle, record_stat_event
from utils.stats.internal.dashboard_repository import TOP_TILES_LIMIT

APP_LOG_TABLE = "app_log"
STAT_EVENT_TABLE = "stat_event"
EXPECTED_RECORD_TABLES = [APP_LOG_TABLE, STAT_EVENT_TABLE]

LOG_LEVEL = "INFO"
LOG_MESSAGE = "db log smoke"
LOG_EXTRA_KEY = "test_name"
LOG_EXTRA_VALUE = "db_logging"
LOG_EXTRA_JSON = f'"{LOG_EXTRA_KEY}": "{LOG_EXTRA_VALUE}"'

PLAYER_ID = "player-1"
OPEN_TILE_EVENT = "OPEN_TILE"
OPEN_TILE_POINT = Point(3, -2)
OPEN_TILE_ID = "tile:3:-2"
OPEN_TILE_SCORE_DELTA = 100
OPEN_TILE_PAYLOAD_JSON = f'"score_delta": {OPEN_TILE_SCORE_DELTA}'

MOVE_EVENT = "MOVE"
MOVE_POINT = Point(4, 5)
MOVE_TILE_ID = "tile:4:5"
MOVE_PAYLOAD_SOURCE = "test"
MOVE_PAYLOAD_JSON = f'"source": "{MOVE_PAYLOAD_SOURCE}"'
SCORE_CHANGE_EVENT = "SCORE_CHANGE"
SCORE_BEFORE = 10
SCORE_AFTER = 30
SCORE_DELTA = SCORE_AFTER - SCORE_BEFORE
SCORE_AFTER_JSON = f'"after_score": {SCORE_AFTER}'
EVENT_VALUE = 1
JOIN_EVENT = "JOIN"
QUIT_EVENT = "QUIT"
CREATE_CURSOR_EVENT = "CREATE_CURSOR"
GRANT_ITEM_EVENT = "GRANT_ITEM"
GRANT_ITEM_AMOUNT = 1
GRANT_ITEM_PAYLOAD_JSON = f'"after_items": {{"bomb": {GRANT_ITEM_AMOUNT}}}'
ACTOR_WITH_SESSION = "player-session"
ACTOR_QUIT_SESSION = "player-quit"
CONNECTION_COUNT = 1
CURSOR_COLOR = 2
CURSOR_WIDTH = 1024
CURSOR_HEIGHT = 768
EXPECTED_ONE_ROW = 1
HEATMAP_TILE_COUNT = TOP_TILES_LIMIT + 1


class RecordDB_TestCase(IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.db_fd, self.db_path = tempfile.mkstemp(suffix=".db")
        self.db_patch = patch.object(BoardConfig, "DB_PATH", new=self.db_path)
        self.db_patch.start()

    def tearDown(self) -> None:
        self.db_patch.stop()
        os.close(self.db_fd)
        os.remove(self.db_path)

    async def asyncSetUp(self) -> None:
        self.db_context = get_db()
        self.db = await self.db_context.__aenter__()
        await set_app_log_table(self.db)
        await set_stat_event_table(self.db)

    async def asyncTearDown(self) -> None:
        await self.db_context.__aexit__(None, None, None)


class RecordTable_TestCase(RecordDB_TestCase):
    async def test_normal(self):
        table_names = await get_record_table_names(self.db)

        self.assertEqual(table_names, EXPECTED_RECORD_TABLES)


class AppLogRepo_TestCase(RecordDB_TestCase):
    async def test_insert(self):
        sink_id = logger.add(AppLogDbSink(self.db_path), level=LOG_LEVEL)
        try:
            logger.bind(**{LOG_EXTRA_KEY: LOG_EXTRA_VALUE}).info(LOG_MESSAGE)
        finally:
            logger.remove(sink_id)

        row = await get_app_log_by_message(self.db, LOG_MESSAGE)

        self.assertEqual(row["level"], LOG_LEVEL)
        self.assertEqual(row["message"], LOG_MESSAGE)
        self.assertIn(LOG_EXTRA_JSON, row["context_json"])


class StatEventRepo_TestCase(RecordDB_TestCase):
    async def test_insert(self):
        await insert_stat_event(
            self.db,
            event_type=OPEN_TILE_EVENT,
            actor_id=PLAYER_ID,
            tile_id=OPEN_TILE_ID,
            x=OPEN_TILE_POINT.x,
            y=OPEN_TILE_POINT.y,
            value=EVENT_VALUE,
            payload={"score_delta": OPEN_TILE_SCORE_DELTA},
        )

        row = await get_stat_event_by_type(self.db, OPEN_TILE_EVENT)

        self.assertEqual(row["event_type"], OPEN_TILE_EVENT)
        self.assertEqual(row["actor_id"], PLAYER_ID)
        self.assertEqual(row["tile_id"], OPEN_TILE_ID)
        self.assertEqual(row["x"], OPEN_TILE_POINT.x)
        self.assertEqual(row["y"], OPEN_TILE_POINT.y)
        self.assertEqual(row["value"], EVENT_VALUE)
        self.assertIn(OPEN_TILE_PAYLOAD_JSON, row["payload_json"])

    async def test_get_total_count_and_observed_range(self):
        await insert_stat_event(
            self.db,
            event_type=JOIN_EVENT,
            actor_id=ACTOR_WITH_SESSION,
            value=EVENT_VALUE,
            payload={"connection_count": CONNECTION_COUNT},
        )

        total_count = await get_total_stat_event_count(self.db)
        observed_range = await get_stat_event_observed_range(self.db)

        self.assertEqual(total_count, EXPECTED_ONE_ROW)
        self.assertIsNotNone(observed_range["first_seen_at"])
        self.assertIsNotNone(observed_range["last_seen_at"])

    async def test_record_stat_event(self):
        await record_stat_event(
            MOVE_EVENT,
            actor_id=PLAYER_ID,
            point=MOVE_POINT,
            value=EVENT_VALUE,
            payload={"source": MOVE_PAYLOAD_SOURCE},
        )

        row = await get_stat_event_by_type(self.db, MOVE_EVENT)

        self.assertEqual(row["event_type"], MOVE_EVENT)
        self.assertEqual(row["actor_id"], PLAYER_ID)
        self.assertEqual(row["tile_id"], MOVE_TILE_ID)
        self.assertEqual(row["x"], MOVE_POINT.x)
        self.assertEqual(row["y"], MOVE_POINT.y)
        self.assertEqual(row["value"], EVENT_VALUE)
        self.assertIn(MOVE_PAYLOAD_JSON, row["payload_json"])


class LifecycleRecorder_TestCase(RecordDB_TestCase):
    def _cursor(self, *, score: int = 0, bomb: int = 0):
        return Cursor.create(
            id=PLAYER_ID,
            position=MOVE_POINT,
            width=CURSOR_WIDTH,
            height=CURSOR_HEIGHT,
            score=score,
            items=Items.from_dict({"bomb": bomb}),
            color=Color.BLUE,
        )

    async def test_record_hlife_with_caller_id_records_score_change(self):
        before = self._cursor(score=SCORE_BEFORE)
        after = self._cursor(score=SCORE_AFTER)
        hlife = HLife.create(
            handler_name="CursorHandler",
            method_name="increase_score",
            params=Parameter(args=(before, SCORE_DELTA), kwargs={}),
        )
        hlife.set_snapshot(before=before, after=after)
        hlife.caller_id = "receiver-caller"

        record_lifecycle(hlife)

        row = await get_stat_event_by_type(self.db, SCORE_CHANGE_EVENT)

        self.assertEqual(row["event_type"], SCORE_CHANGE_EVENT)
        self.assertEqual(row["actor_id"], PLAYER_ID)
        self.assertEqual(row["tile_id"], MOVE_TILE_ID)
        self.assertEqual(row["value"], SCORE_DELTA)
        self.assertIn(SCORE_AFTER_JSON, row["payload_json"])

    async def test_record_hlife_with_caller_id_records_grant_item(self):
        before = self._cursor(bomb=0)
        after = self._cursor(bomb=GRANT_ITEM_AMOUNT)
        hlife = HLife.create(
            handler_name="CursorHandler",
            method_name="grant_item",
            params=Parameter(args=(before, ItemType.BOMB, GRANT_ITEM_AMOUNT), kwargs={}),
        )
        hlife.set_snapshot(before=before, after=after)
        hlife.caller_id = "receiver-caller"

        record_lifecycle(hlife)

        row = await get_stat_event_by_type(self.db, GRANT_ITEM_EVENT)

        self.assertEqual(row["event_type"], GRANT_ITEM_EVENT)
        self.assertEqual(row["actor_id"], PLAYER_ID)
        self.assertEqual(row["tile_id"], MOVE_TILE_ID)
        self.assertEqual(row["value"], GRANT_ITEM_AMOUNT)
        self.assertIn(GRANT_ITEM_PAYLOAD_JSON, row["payload_json"])


class DashboardRepository_TestCase(RecordDB_TestCase):
    async def test_tile_heatmap_keeps_all_move_tiles(self):
        for x in range(HEATMAP_TILE_COUNT):
            point = Point(x, 0)
            await insert_stat_event(
                self.db,
                event_type=MOVE_EVENT,
                actor_id=PLAYER_ID,
                tile_id=f"tile:{point.x}:{point.y}",
                x=point.x,
                y=point.y,
                value=EVENT_VALUE,
                payload={},
            )
        await insert_stat_event(
            self.db,
            event_type=CREATE_CURSOR_EVENT,
            actor_id=PLAYER_ID,
            tile_id=OPEN_TILE_ID,
            x=OPEN_TILE_POINT.x,
            y=OPEN_TILE_POINT.y,
            value=EVENT_VALUE,
            payload={},
        )

        dashboard = await get_dashboard()

        self.assertEqual(len(dashboard["tiles"]), TOP_TILES_LIMIT)
        self.assertEqual(len(dashboard["tile_heatmap"]), HEATMAP_TILE_COUNT)
        self.assertNotIn(OPEN_TILE_ID, [
            tile["tile_id"]
            for tile in dashboard["tile_heatmap"]
        ])

    async def test_last_known_cursor_keeps_join_without_quit(self):
        await insert_stat_event(
            self.db,
            event_type=JOIN_EVENT,
            actor_id=ACTOR_WITH_SESSION,
            value=EVENT_VALUE,
            payload={"connection_count": CONNECTION_COUNT},
        )
        await insert_stat_event(
            self.db,
            event_type=CREATE_CURSOR_EVENT,
            actor_id=ACTOR_WITH_SESSION,
            tile_id=OPEN_TILE_ID,
            x=OPEN_TILE_POINT.x,
            y=OPEN_TILE_POINT.y,
            value=EVENT_VALUE,
            payload={
                "color": CURSOR_COLOR,
                "width": CURSOR_WIDTH,
                "height": CURSOR_HEIGHT,
            },
        )
        await insert_stat_event(
            self.db,
            event_type=MOVE_EVENT,
            actor_id=ACTOR_WITH_SESSION,
            tile_id=MOVE_TILE_ID,
            x=MOVE_POINT.x,
            y=MOVE_POINT.y,
            value=EVENT_VALUE,
            payload={},
        )
        await insert_stat_event(
            self.db,
            event_type=SCORE_CHANGE_EVENT,
            actor_id=ACTOR_WITH_SESSION,
            tile_id=MOVE_TILE_ID,
            x=MOVE_POINT.x,
            y=MOVE_POINT.y,
            value=SCORE_DELTA,
            payload={"score_delta": SCORE_DELTA},
        )

        dashboard = await get_dashboard()
        cursor = dashboard["last_known_cursors"][0]

        self.assertEqual(dashboard["stored"]["total_events"], 4)
        self.assertEqual(len(dashboard["last_known_cursors"]), EXPECTED_ONE_ROW)
        self.assertEqual(cursor["cursor_id"], ACTOR_WITH_SESSION)
        self.assertEqual(cursor["tile_id"], MOVE_TILE_ID)
        self.assertEqual(cursor["color"], CURSOR_COLOR)
        self.assertEqual(cursor["score"], SCORE_DELTA)
        self.assertEqual(cursor["window"]["width"], CURSOR_WIDTH)

    async def test_last_known_cursor_excludes_quit_session(self):
        await insert_stat_event(
            self.db,
            event_type=JOIN_EVENT,
            actor_id=ACTOR_QUIT_SESSION,
            value=EVENT_VALUE,
            payload={"connection_count": CONNECTION_COUNT},
        )
        await insert_stat_event(
            self.db,
            event_type=QUIT_EVENT,
            actor_id=ACTOR_QUIT_SESSION,
            value=EVENT_VALUE,
            payload={"connection_count": 0},
        )

        dashboard = await get_dashboard()

        self.assertEqual(dashboard["stored"]["total_events"], 2)
        self.assertEqual(dashboard["last_known_cursors"], [])


if __name__ == "__main__":
    from unittest import main
    main()
