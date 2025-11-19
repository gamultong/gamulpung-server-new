from handler.board import BoardHandler
from config import BoardConfig
from data.board import Point, Tile, Tiles, PointRange, Section
from core.event import Event
from data.payload import ServerMessage
from data.cursor import Cursor
from data.conn import Message
from .map.case2 import CLOSED_TILE, OPENED_TILE
from .map.helpers import setup_case_2_map
from server import app
from typing import cast
from unittest.mock import AsyncMock, call, patch
from tests.utils import assert_wait_call, TestClientManager, set_board
from tests.utils import TestCase
from datetime import timedelta

SET_WINDOW_MSG = {
    "header": {"event": "SET-WINDOW"},
    "payload": {"width": 1, "height": 1},
}
OPEN_TILES_MSG = {
    "header": {"event": "OPEN-TILES"},
    "payload": {
        "position": {
            "x": -1,
            "y": 0
        }
    },
}
CL_A = "Example_A"

clinetmanager = (
    TestClientManager(app)
    .append_client(CL_A)
)


class ExplosionScenario(TestCase.IntegrationTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.section_length_patch = patch.object(BoardConfig, "LENGTH", new=2)
        self.section_length_patch.start()

    def tearDown(self) -> None:
        self.section_length_patch.stop()
        super().tearDown()

    async def asyncSetUp(self) -> None:
        await super().asyncSetUp()

    async def asyncTearDown(self) -> None:
        await super().asyncTearDown()

    @set_board(setup_case_2_map)
    @clinetmanager
    def test_normal(self, tcm: TestClientManager):
        cl_a = tcm.get_client(CL_A)
        cl_a.ws.send_json(SET_WINDOW_MSG)
        cl_a.ws.send_json(OPEN_TILES_MSG)

        conn_a_send_mock = cast(AsyncMock, cl_a.conn.send)

        event = Message(
            Event(
                event_name="EXPLOSION",
                payload=ServerMessage.Explosion(
                    Point(-1, 0)
                )
            )
        )
        assert_wait_call(
            conn_a_send_mock,
            call=call(event)
        )

        event = Message(
            Event(
                event_name="CURSORS-STATE",
                payload=ServerMessage.CursorsState(
                    [Cursor.create(CL_A, width=1, height=1, active_at=self.now+timedelta(seconds=30))]
                )
            )
        )

        assert_wait_call(
            conn_a_send_mock,
            call=call(event)
        )

        event = Message(
            Event(
                event_name="SCOREBOARD-STATE",
                payload=ServerMessage.ScoreBoardState(
                    scoreboard={
                        1: 0
                    }
                )
            )
        )

        assert_wait_call(
            conn_a_send_mock,
            call=call(event)
        )


if __name__ == "__main__":
    from unittest import main
    main()
